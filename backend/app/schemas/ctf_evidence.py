import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CtfEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ctf_challenge_id: uuid.UUID
    evidence_type: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    description: str | None
    notes: str | None
    is_public: bool
    uploaded_at: datetime


class CtfEvidenceUpdate(BaseModel):
    description: str | None = None
    notes: str | None = None
    is_public: bool | None = None
