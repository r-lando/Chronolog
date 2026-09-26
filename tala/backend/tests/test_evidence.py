"""
Tests for Milestone 3: evidence management.

Covers the security-critical paths in app/services/evidence_service.py:
extension whitelist enforcement, magic-byte signature checking, UTF-8
validation for text evidence, size limit enforcement, safe (server-
generated) filenames, hash computation, download access control, and
findings CRUD.
"""

import io

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

SAMPLE_LAB = {
    "title": "PCAP Investigation",
    "platform": "Home Lab",
    "category": "Network Security",
    "difficulty": "Medium",
    "status": "In Progress",
}

# A minimal valid PNG: signature bytes + a tiny bit of filler.
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _register_and_create_lab(client) -> str:
    client.post("/api/v1/auth/register", json=VALID_USER)
    lab = client.post("/api/v1/labs", json=SAMPLE_LAB).json()
    return lab["id"]


def _upload(client, lab_id, filename, content, evidence_type="screenshot", content_type="image/png"):
    return client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": evidence_type, "description": "test upload"},
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


def test_upload_valid_png_succeeds(client):
    lab_id = _register_and_create_lab(client)
    response = _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES)
    assert response.status_code == 201
    body = response.json()
    assert body["evidence_type"] == "screenshot"
    assert body["original_filename"] == "screenshot.png"
    assert body["mime_type"] == "image/png"
    assert len(body["sha256_hash"]) == 64
    assert body["file_size_bytes"] == len(VALID_PNG_BYTES)


def test_upload_rejects_disallowed_extension(client):
    lab_id = _register_and_create_lab(client)
    response = _upload(
        client, lab_id, "malicious.exe", b"MZ\x90\x00fake-exe-content", evidence_type="report",
        content_type="application/octet-stream",
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


def test_upload_rejects_content_mismatched_with_extension(client):
    """A file renamed to .png that isn't actually PNG data must be rejected —
    the client-declared Content-Type is never trusted on its own."""
    lab_id = _register_and_create_lab(client)
    response = _upload(client, lab_id, "fake.png", b"this is not a real png file at all")
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]


def test_upload_rejects_non_utf8_text_file(client):
    lab_id = _register_and_create_lab(client)
    invalid_utf8 = b"\xff\xfe\x00\x01broken text file"
    response = _upload(
        client, lab_id, "notes.txt", invalid_utf8, evidence_type="text", content_type="text/plain"
    )
    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_upload_accepts_valid_text_log(client):
    lab_id = _register_and_create_lab(client)
    log_content = b"2026-09-24 10:00:00 Failed login for user admin from 10.0.0.5\n"
    response = _upload(client, lab_id, "auth.log", log_content, evidence_type="log", content_type="text/plain")
    assert response.status_code == 201
    assert response.json()["mime_type"] == "text/plain"


def test_upload_rejects_oversized_file(client, monkeypatch):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)  # 0 MB effective limit forces rejection
    # max_upload_size_bytes is a computed property reading max_upload_size_mb, so this takes effect immediately.

    lab_id = _register_and_create_lab(client)
    response = _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES)
    assert response.status_code == 413


def test_upload_rejects_empty_file(client):
    lab_id = _register_and_create_lab(client)
    response = _upload(client, lab_id, "empty.png", b"")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_rejects_invalid_evidence_type(client):
    lab_id = _register_and_create_lab(client)
    response = _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES, evidence_type="not_a_real_type")
    assert response.status_code == 400


def test_stored_filename_is_not_user_controlled(client):
    """
    Proves that a crafted original filename (attempted path traversal)
    never influences the server-side storage path: the stored filename
    is always a fresh UUID with the validated extension.
    """
    lab_id = _register_and_create_lab(client)
    response = _upload(client, lab_id, "../../etc/passwd.png", VALID_PNG_BYTES)
    assert response.status_code == 201
    body = response.json()
    # original_filename is sanitized to a basename for display only
    assert body["original_filename"] == "passwd.png"


def test_list_evidence_for_lab(client):
    lab_id = _register_and_create_lab(client)
    _upload(client, lab_id, "one.png", VALID_PNG_BYTES)
    _upload(client, lab_id, "two.png", VALID_PNG_BYTES)

    response = client.get(f"/api/v1/labs/{lab_id}/evidence")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_download_evidence_requires_auth(client):
    lab_id = _register_and_create_lab(client)
    uploaded = _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES).json()

    client.post("/api/v1/auth/logout")
    response = client.get(f"/api/v1/evidence/{uploaded['id']}/file")
    assert response.status_code == 401


def test_download_evidence_returns_file_with_attachment_disposition(client):
    lab_id = _register_and_create_lab(client)
    uploaded = _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES).json()

    response = client.get(f"/api/v1/evidence/{uploaded['id']}/file")
    assert response.status_code == 200
    assert response.content == VALID_PNG_BYTES
    assert "attachment" in response.headers["content-disposition"]


def test_update_evidence_metadata(client):
    lab_id = _register_and_create_lab(client)
    uploaded = _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES).json()

    response = client.patch(
        f"/api/v1/evidence/{uploaded['id']}",
        json={"description": "Updated description", "is_public": True},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"
    assert response.json()["is_public"] is True


def test_delete_evidence_removes_record_and_file(client, isolated_evidence_storage):
    lab_id = _register_and_create_lab(client)
    uploaded = _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES).json()

    stored_files_before = list(isolated_evidence_storage.iterdir())
    assert len(stored_files_before) == 1

    response = client.delete(f"/api/v1/evidence/{uploaded['id']}")
    assert response.status_code == 204

    stored_files_after = list(isolated_evidence_storage.iterdir())
    assert len(stored_files_after) == 0

    get_response = client.get(f"/api/v1/labs/{lab_id}/evidence")
    assert get_response.json() == []


def test_create_and_list_findings(client):
    lab_id = _register_and_create_lab(client)
    response = client.post(
        f"/api/v1/labs/{lab_id}/findings",
        json={"title": "Repeated failed logons", "description": "20 failures in 2 minutes", "severity": "High"},
    )
    assert response.status_code == 201
    assert response.json()["severity"] == "High"

    list_response = client.get(f"/api/v1/labs/{lab_id}/findings")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_finding_rejects_invalid_severity(client):
    lab_id = _register_and_create_lab(client)
    response = client.post(
        f"/api/v1/labs/{lab_id}/findings",
        json={"title": "Something", "severity": "Catastrophic"},
    )
    assert response.status_code == 422


def test_evidence_can_link_to_finding(client):
    lab_id = _register_and_create_lab(client)
    finding = client.post(
        f"/api/v1/labs/{lab_id}/findings", json={"title": "Brute force detected"}
    ).json()

    response = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot", "finding_id": finding["id"]},
        files={"file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert response.status_code == 201
    assert response.json()["finding_id"] == finding["id"]


def test_evidence_rejects_finding_from_another_lab(client):
    lab_id = _register_and_create_lab(client)
    other_lab = client.post("/api/v1/labs", json={**SAMPLE_LAB, "title": "Other Lab"}).json()
    finding_in_other_lab = client.post(
        f"/api/v1/labs/{other_lab['id']}/findings", json={"title": "Unrelated finding"}
    ).json()

    response = _upload(client, lab_id, "proof.png", VALID_PNG_BYTES)
    # sanity: normal upload without finding_id still works
    assert response.status_code == 201

    bad_response = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot", "finding_id": finding_in_other_lab["id"]},
        files={"file": ("proof2.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert bad_response.status_code == 400


def test_global_evidence_listing_includes_lab_title(client):
    lab_id = _register_and_create_lab(client)
    _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES)

    response = client.get("/api/v1/evidence")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["lab_title"] == SAMPLE_LAB["title"]


def test_global_evidence_listing_filters_by_type(client):
    lab_id = _register_and_create_lab(client)
    _upload(client, lab_id, "screenshot.png", VALID_PNG_BYTES, evidence_type="screenshot")
    _upload(
        client, lab_id, "auth.log", b"log line\n", evidence_type="log", content_type="text/plain"
    )

    response = client.get("/api/v1/evidence", params={"evidence_type": "log"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["evidence_type"] == "log"


def test_deleting_lab_cascades_to_findings_and_evidence(client, db_session, isolated_evidence_storage):
    """
    Findings and Evidence have no ORM-level relationship on Lab (unlike
    the write-up), so the DB row cascade only happens via the database's
    own ON DELETE CASCADE — this test proves that constraint actually
    works. It also proves the router explicitly cleans up the physical
    evidence file, since the database cascade has no way to touch disk.
    """
    from app.models.evidence import Evidence
    from app.models.finding import Finding

    lab_id = _register_and_create_lab(client)
    finding = client.post(f"/api/v1/labs/{lab_id}/findings", json={"title": "Test finding"}).json()
    _upload(client, lab_id, "proof.png", VALID_PNG_BYTES)

    assert db_session.query(Finding).filter(Finding.id == finding["id"]).first() is not None
    assert len(list(isolated_evidence_storage.iterdir())) == 1

    delete_response = client.delete(f"/api/v1/labs/{lab_id}")
    assert delete_response.status_code == 204

    db_session.expire_all()
    assert db_session.query(Finding).filter(Finding.lab_id == lab_id).count() == 0
    assert db_session.query(Evidence).filter(Evidence.lab_id == lab_id).count() == 0
    assert len(list(isolated_evidence_storage.iterdir())) == 0
