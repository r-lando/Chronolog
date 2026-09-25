import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID

# Pure many-to-many junction — no extra columns, so a Core Table is
# simpler and more honest than a full ORM model with nothing to add.
lab_tags = Table(
    "lab_tags",
    Base.metadata,
    Column("lab_id", GUID(), ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", GUID(), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    labs: Mapped[list["Lab"]] = relationship(secondary=lab_tags, back_populates="tags")


# Imported at the bottom to resolve the "Lab" forward reference above,
# mirroring the same pattern used in lab.py for its "Tag" reference.
from app.models.lab import Lab  # noqa: E402
