import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID

lab_skills = Table(
    "lab_skills",
    Base.metadata,
    Column("lab_id", GUID(), ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", GUID(), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(Base):
    """
    A shared master-list entry (e.g. "Log Analysis", "Threat Hunting").
    Skills are global reference data, not owned by a specific user —
    what's user-scoped is which labs (owned by that user) reference a
    given skill, which is where all the "X labs completed" stats in the
    Skills page come from (see app/services/skill_service.py).
    """

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    labs: Mapped[list["Lab"]] = relationship(secondary=lab_skills, back_populates="skills")


# Imported at the bottom to resolve the "Lab" forward reference above,
# mirroring the circular-import-safe pattern used in lab.py/tag.py.
from app.models.lab import Lab  # noqa: E402
