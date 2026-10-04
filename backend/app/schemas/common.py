import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class NameAttach(BaseModel):
    """Body for attach-by-name endpoints (skills, tools) — creates the item if it doesn't exist yet."""

    name: str = Field(min_length=1, max_length=100)


class NameIdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class TechniqueSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    technique_id: str
    name: str


class LabSummaryOut(BaseModel):
    """A trimmed-down lab representation for embedding in skill/tool/technique detail views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: str
    difficulty: str
    status: str
    date_completed: date | None
