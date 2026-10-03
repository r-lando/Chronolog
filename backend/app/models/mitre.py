import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID


class MitreTechnique(Base):
    """
    A single MITRE ATT&CK technique from a curated, seeded reference
    list (see app/seed/seed_data.py) — not user-created, unlike tags,
    skills, or tools. Users can only map labs to techniques that already
    exist here, which is what stops a mapping from being fabricated out
    of thin air: you can pick T1110, but you can't invent "T9999".
    """

    __tablename__ = "mitre_techniques"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    technique_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # e.g. "T1110"
    sub_technique_id: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "T1059.001"
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    tactic: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    lab_techniques: Mapped[list["LabTechnique"]] = relationship(back_populates="technique")


class LabTechnique(Base):
    """
    Association object (not a plain many-to-many secondary table)
    because the mapping itself carries data: a required justification
    explaining why this technique applies to this lab. This is the
    schema-level guardrail against fabricated ATT&CK mappings — the API
    layer additionally enforces a minimum justification length (see
    app/schemas/mitre.py).
    """

    __tablename__ = "lab_techniques"

    lab_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True)
    technique_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("mitre_techniques.id", ondelete="CASCADE"), primary_key=True
    )
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    lab: Mapped["Lab"] = relationship(back_populates="techniques")
    technique: Mapped["MitreTechnique"] = relationship(back_populates="lab_techniques")


# Imported at the bottom to resolve the "Lab" forward reference above,
# mirroring the circular-import-safe pattern used elsewhere in models/.
from app.models.lab import Lab  # noqa: E402
