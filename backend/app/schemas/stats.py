import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import LabSummaryOut


class ChartPoint(BaseModel):
    """One labelled bar/point in a chart. `count` is always a real count from stored data."""

    label: str
    count: int


class OverviewOut(BaseModel):
    labs_completed: int
    ctf_challenges_solved: int
    total_learning_hours: float
    current_streak_days: int
    skills_practiced: int
    tools_used: int
    techniques_practiced: int
    labs_completed_this_month: int
    # Completed labs with no date_completed can't be placed on the
    # timeline or in "this month". Surfacing the number (instead of
    # silently dropping them) lets the UI tell the user why totals differ.
    completed_labs_without_date: int


class RecentCtfChallengeOut(BaseModel):
    id: uuid.UUID
    ctf_event_id: uuid.UUID
    title: str
    category: str
    status: str
    event_name: str
    created_at: datetime


class RecentSkillOut(BaseModel):
    id: uuid.UUID
    name: str
    last_practiced: date


class RecentActivityOut(BaseModel):
    recent_labs: list[LabSummaryOut]
    recent_ctf_challenges: list[RecentCtfChallengeOut]
    recently_practiced_skills: list[RecentSkillOut]
