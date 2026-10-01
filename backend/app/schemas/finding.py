import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import FINDING_SEVERITIES


class FindingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    severity: str | None = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str | None) -> str | None:
        if v is not None and v not in FINDING_SEVERITIES:
            raise ValueError(f"severity must be one of: {', '.join(FINDING_SEVERITIES)}")
        return v


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lab_id: uuid.UUID
    title: str
    description: str | None
    severity: str | None
    created_at: datetime
