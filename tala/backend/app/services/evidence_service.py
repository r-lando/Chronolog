"""
Evidence upload security.

This is the most security-sensitive code path in TALA, since it's the
one place a person's browser sends arbitrary file bytes to the server.
The design follows a whitelist-first approach rather than trying to
blocklist "known bad" files, which is much harder to get right:

1. Extension must be in ALLOWED_EXTENSIONS. Anything else (.exe, .php,
   .sh, .html, ...) is rejected outright — there is no path for an
   unlisted extension to ever be accepted.
2. For extensions with a known binary signature (images, PDF, PCAP),
   the first bytes of the actual file content must match that
   signature. This catches someone renaming a script to "screenshot.png"
   — the client-declared Content-Type header is never trusted alone,
   since it's fully attacker-controlled.
3. For plain-text extensions (.log, .txt, .md, .json, .yaml, .conf,
   .csv, .xml), the content must decode as valid UTF-8. This is a
   cheap, honest check that the file actually looks like the text it
   claims to be, without requiring a heavy content-sniffing library.
4. Size is enforced by reading up to (limit + 1) bytes and rejecting if
   that boundary is crossed — not by trusting the Content-Length header,
   which a client can misreport.
5. The file is saved under a random UUID-based name with the validated
   extension. The original filename is kept only as a display string
   (and is basename-sanitized) — it is never used to construct a
   filesystem path, which is what prevents path traversal.
"""

import hashlib
import os
import uuid
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile, status

from app.config import Settings

# extension -> (list of magic-byte signatures to check, is_text_format)
# A file type with an empty signature list skips the binary-signature
# check and instead goes through the UTF-8 text validation below.
_MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".gif": [b"GIF87a", b"GIF89a"],
    ".pdf": [b"%PDF-"],
    ".pcap": [b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4"],
    ".pcapng": [b"\x0a\x0d\x0d\x0a"],
}

_TEXT_EXTENSIONS = {".log", ".txt", ".md", ".json", ".yaml", ".yml", ".conf", ".cfg", ".csv", ".xml"}

ALLOWED_EXTENSIONS = set(_MAGIC_SIGNATURES.keys()) | _TEXT_EXTENSIONS

_DEFAULT_MIME_BY_EXTENSION = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".pcap": "application/vnd.tcpdump.pcap",
    ".pcapng": "application/octet-stream",
    ".log": "text/plain",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".json": "application/json",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".conf": "text/plain",
    ".cfg": "text/plain",
    ".csv": "text/csv",
    ".xml": "application/xml",
}


@dataclass
class ValidatedUpload:
    stored_filename: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    absolute_path: str


def _get_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename.lower())
    return ext


async def _read_with_size_limit(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    chunk_size = 1024 * 1024  # 1 MB at a time, so we never buffer more than necessary before failing fast

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the maximum upload size of {max_bytes // (1024 * 1024)} MB.",
            )
        chunks.append(chunk)

    return b"".join(chunks)


def _validate_signature(extension: str, content: bytes) -> None:
    signatures = _MAGIC_SIGNATURES.get(extension)
    if not signatures:
        return  # not a signature-checked type — handled by the text check instead

    if not any(content.startswith(sig) for sig in signatures):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content does not match the expected format for '{extension}' files.",
        )


def _validate_text_content(extension: str, content: bytes) -> None:
    if extension not in _TEXT_EXTENSIONS:
        return

    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{extension}' evidence must be valid UTF-8 text.",
        )


async def validate_and_store_upload(file: UploadFile, settings: Settings) -> ValidatedUpload:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    extension = _get_extension(file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{extension}' is not allowed. Allowed types: {allowed}",
        )

    content = await _read_with_size_limit(file, settings.max_upload_size_bytes)
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    _validate_signature(extension, content)
    _validate_text_content(extension, content)

    # The stored filename is entirely server-generated — no part of the
    # user-supplied filename is used here, which is what makes path
    # traversal via a crafted filename structurally impossible.
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    absolute_path = os.path.join(settings.evidence_storage_path, stored_filename)

    os.makedirs(settings.evidence_storage_path, exist_ok=True)
    with open(absolute_path, "wb") as f:
        f.write(content)

    sha256_hash = hashlib.sha256(content).hexdigest()
    safe_original_name = os.path.basename(file.filename)[:255]

    return ValidatedUpload(
        stored_filename=stored_filename,
        original_filename=safe_original_name,
        mime_type=_DEFAULT_MIME_BY_EXTENSION.get(extension, "application/octet-stream"),
        file_size_bytes=len(content),
        sha256_hash=sha256_hash,
        absolute_path=absolute_path,
    )


def resolve_evidence_path(stored_filename: str, settings: Settings) -> str:
    """
    Resolves an evidence file's path and defensively verifies it still
    lands inside the evidence storage directory. stored_filename always
    comes from our own database (never directly from a request), so
    this is defense-in-depth rather than the primary control.
    """
    storage_root = os.path.realpath(settings.evidence_storage_path)
    candidate = os.path.realpath(os.path.join(storage_root, stored_filename))

    if not candidate.startswith(storage_root + os.sep):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found")

    if not os.path.isfile(candidate):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found")

    return candidate


def delete_evidence_file(stored_filename: str, settings: Settings) -> None:
    try:
        path = resolve_evidence_path(stored_filename, settings)
        os.remove(path)
    except HTTPException:
        pass  # already gone — deleting the DB record should still proceed
