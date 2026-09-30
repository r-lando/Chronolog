import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import LabSummaryOut, NameIdOut, TechniqueSummaryOut


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None
    description: str | None


class SkillWithStatsOut(SkillOut):
    """
    Deliberately measurable activity counts, not a self-reported
    proficiency percentage — see the product spec's requirement that
    skill "strength" is shown as labs/tools/techniques counts, never as
    a number the user just types in.
    """

    lab_count: int
    last_practiced: date | None


class SkillDetailOut(SkillWithStatsOut):
    related_labs: list[LabSummaryOut]
    related_tools: list[NameIdOut]
    related_techniques: list[TechniqueSummaryOut]
