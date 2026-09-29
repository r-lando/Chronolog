import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID

lab_tools = Table(
    "lab_tools",
    Base.metadata,
    Column("lab_id", GUID(), ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
    Column("tool_id", GUID(), ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
)


class Tool(Base):
    """A shared master-list entry (e.g. "Wireshark", "Splunk"). See Skill's docstring — same design."""

    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    labs: Mapped[list["Lab"]] = relationship(secondary=lab_tools, back_populates="tools")


# Imported at the bottom to resolve the "Lab" forward reference above,
# mirroring the circular-import-safe pattern used in lab.py/tag.py.
from app.models.lab import Lab  # noqa: E402
