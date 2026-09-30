import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import CTF_CATEGORIES, CTF_STATUSES, LAB_DIFFICULTIES
from app.schemas.mitre import LabTechniqueAttach, LabTechniqueOut
from app.schemas.skill import SkillOut
from app.schemas.tool import ToolOut


class CtfEventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    platform: str | None = Field(default=None, max_length=100)
    event_date: date | None = None


class CtfEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    platform: str | None
    event_date: date | None
    created_at: datetime


class CtfChallengeBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str
    difficulty: str
    status: str = "Unsolved"
    time_spent_minutes: int | None = Field(default=None, ge=0)
    description: str | None = None
    solution_writeup: str | None = None
    lessons_learned: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CTF_CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(CTF_CATEGORIES)}")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        if v not in LAB_DIFFICULTIES:
            raise ValueError(f"difficulty must be one of: {', '.join(LAB_DIFFICULTIES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in CTF_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(CTF_STATUSES)}")
        return v


class CtfChallengeCreate(CtfChallengeBase):
    pass


class CtfChallengeUpdate(CtfChallengeBase):
    pass


class CtfChallengeOut(CtfChallengeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ctf_event_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    skills: list[SkillOut] = []
    tools: list[ToolOut] = []
    techniques: list[LabTechniqueOut] = []


class CtfEventDetailOut(CtfEventOut):
    challenges: list[CtfChallengeOut] = []


class CtfOptionsOut(BaseModel):
    categories: list[str]
    difficulties: list[str]
    statuses: list[str]


# Reused directly — the shape (technique_id + justification, min length
# enforced) is identical to a lab's technique mapping.
CtfChallengeTechniqueAttach = LabTechniqueAttach
