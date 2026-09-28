import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import LabSummaryOut, NameIdOut, TechniqueSummaryOut


class ToolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None
    description: str | None


class ToolWithStatsOut(ToolOut):
    lab_count: int
    last_used: date | None


class ToolDetailOut(ToolWithStatsOut):
    related_labs: list[LabSummaryOut]
    related_skills: list[NameIdOut]
    related_techniques: list[TechniqueSummaryOut]
