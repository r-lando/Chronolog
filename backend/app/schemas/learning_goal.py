import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import LabSummaryOut


class LearningGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    parent_goal_id: uuid.UUID | None = None
    related_skill_id: uuid.UUID | None = None
    target_notes: str | None = None


class LearningGoalUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    parent_goal_id: uuid.UUID | None = None
    related_skill_id: uuid.UUID | None = None
    target_notes: str | None = None


class LearningGoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    parent_goal_id: uuid.UUID | None
    related_skill_id: uuid.UUID | None
    target_notes: str | None
    created_at: datetime


class CtfChallengeSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    status: str
    category: str


class LearningGoalProgressOut(BaseModel):
    """
    Progress is always a count of real documented activity — never a
    self-reported percentage. A goal with no related_skill (a grouping
    node like "SOC Analyst") instead shows a simple rollup of how many
    of its direct children have any recorded activity.
    """

    goal_id: uuid.UUID
    has_related_skill: bool
    labs_completed: int = 0
    related_labs: list[LabSummaryOut] = []
    related_ctf_challenges: list[CtfChallengeSummaryOut] = []
    recommended_next_activity: str
    child_count: int = 0
    children_with_activity: int = 0
