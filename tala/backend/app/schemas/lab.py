import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import LAB_CATEGORIES, LAB_DIFFICULTIES, LAB_STATUSES


def _validate_choice(value: str, allowed: list[str], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of: {', '.join(allowed)}")
    return value


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class LabBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    platform: str | None = Field(default=None, max_length=100)
    category: str
    difficulty: str
    status: str = "Planned"
    date_started: date | None = None
    date_completed: date | None = None
    time_spent_minutes: int | None = Field(default=None, ge=0)
    description: str | None = None
    objective: str | None = None
    environment: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        return _validate_choice(v, LAB_CATEGORIES, "category")

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        return _validate_choice(v, LAB_DIFFICULTIES, "difficulty")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        return _validate_choice(v, LAB_STATUSES, "status")

    @field_validator("date_completed")
    @classmethod
    def completed_not_before_started(cls, v: date | None, info):
        started = info.data.get("date_started")
        if v and started and v < started:
            raise ValueError("date_completed cannot be before date_started")
        return v


class LabCreate(LabBase):
    pass


class LabUpdate(LabBase):
    pass


class LabStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        return _validate_choice(v, LAB_STATUSES, "status")


class LabWriteupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    methodology: str | None = None
    findings: str | None = None
    analysis: str | None = None
    lessons_learned: str | None = None
    reflection: str | None = None
    next_steps: str | None = None
    format: str = "markdown"
    updated_at: datetime


class LabWriteupUpdate(BaseModel):
    methodology: str | None = None
    findings: str | None = None
    analysis: str | None = None
    lessons_learned: str | None = None
    reflection: str | None = None
    next_steps: str | None = None


class LabOut(LabBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_portfolio_ready: bool
    portfolio_slug: str | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut] = []


class LabDetailOut(LabOut):
    writeup: LabWriteupOut | None = None


class LabOptionsOut(BaseModel):
    """Single source of truth for frontend dropdowns, mirroring app.constants."""

    categories: list[str]
    difficulties: list[str]
    statuses: list[str]


class TagAttach(BaseModel):
    name: str = Field(min_length=1, max_length=50)
