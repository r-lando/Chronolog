from datetime import datetime

from pydantic import BaseModel


class PortfolioStatusUpdate(BaseModel):
    is_portfolio_ready: bool


class PublicTechniqueOut(BaseModel):
    technique_id: str
    sub_technique_id: str | None
    name: str
    tactic: str
    justification: str


class PublicEvidenceOut(BaseModel):
    id: str
    evidence_type: str
    original_filename: str
    description: str | None
    file_url: str
    # Deliberately excluded: `notes` (the user's private annotation field)
    # and anything about internal storage paths.


class PublicLabOut(BaseModel):
    """
    The entire set of fields ever returned by the public portfolio
    endpoints. Deliberately excludes: the write-up's `reflection` field,
    every evidence item's `notes` field, and any evidence not explicitly
    marked is_public=True. See app/services/portfolio_service.py for
    where each exclusion is enforced.
    """

    slug: str
    title: str
    category: str
    difficulty: str
    platform: str | None
    summary: str | None
    objective: str | None
    environment: str | None
    methodology: str | None
    findings: str | None
    analysis: str | None
    lessons_learned: str | None
    next_steps: str | None
    skills: list[str]
    tools: list[str]
    techniques: list[PublicTechniqueOut]
    evidence: list[PublicEvidenceOut]
    published_at: datetime


class PublicLabSummaryOut(BaseModel):
    slug: str
    title: str
    category: str
    difficulty: str
    platform: str | None
    summary: str | None
    published_at: datetime
