import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import LabSummaryOut


class MitreTechniqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    technique_id: str
    sub_technique_id: str | None
    name: str
    tactic: str
    description: str | None


class MitreTechniqueWithStatsOut(MitreTechniqueOut):
    lab_count: int
    last_practiced: date | None


class RelatedLabWithJustificationOut(BaseModel):
    lab: LabSummaryOut
    justification: str


class MitreTechniqueDetailOut(MitreTechniqueWithStatsOut):
    related_labs: list[RelatedLabWithJustificationOut]


class LabTechniqueAttach(BaseModel):
    """
    technique_id here is the technique's own database id (from the
    seeded reference list) — not a free-typed MITRE code — so a mapping
    can only ever point at a technique that genuinely exists.

    The justification has a real minimum length on purpose: it's the
    guardrail against rubber-stamped or fabricated ATT&CK mappings.
    "used powershell" (16 chars) passes; "yes" does not.
    """

    technique_id: uuid.UUID
    justification: str = Field(min_length=10, max_length=1000)


class LabTechniqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    technique: MitreTechniqueOut
    justification: str
    created_at: datetime
