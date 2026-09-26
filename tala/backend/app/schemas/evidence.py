import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.constants import EVIDENCE_TYPES


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lab_id: uuid.UUID
    finding_id: uuid.UUID | None
    evidence_type: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    description: str | None
    notes: str | None
    is_public: bool
    uploaded_at: datetime


class EvidenceWithLabOut(EvidenceOut):
    lab_title: str


class EvidenceUpdate(BaseModel):
    description: str | None = None
    notes: str | None = None
    is_public: bool | None = None
    finding_id: uuid.UUID | None = None


def validate_evidence_type(value: str) -> str:
    if value not in EVIDENCE_TYPES:
        raise ValueError(f"evidence_type must be one of: {', '.join(EVIDENCE_TYPES)}")
    return value
