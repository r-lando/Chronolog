import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID


class Lab(Base):
    __tablename__ = "labs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Planned", index=True)

    date_started: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_completed: Mapped[date | None] = mapped_column(Date, nullable=True)
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Portfolio fields live on the schema from the start (avoids a later
    # migration), but the publish workflow itself is built in Milestone 9.
    is_portfolio_ready: Mapped[bool] = mapped_column(default=False, nullable=False)
    portfolio_slug: Mapped[str | None] = mapped_column(String(220), unique=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    writeup: Mapped["LabWriteup"] = relationship(
        back_populates="lab", uselist=False, cascade="all, delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary="lab_tags", back_populates="labs"
    )


class LabWriteup(Base):
    """
    One-to-one with Lab. Split into its own table because it's a large
    text payload that's logically distinct from lab metadata — most
    list/filter queries never need to touch this table at all.
    """

    __tablename__ = "lab_writeups"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lab_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("labs.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    reflection: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="markdown")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    lab: Mapped["Lab"] = relationship(back_populates="writeup")


# Imported here (rather than at the top) to avoid a circular import between
# lab.py and tag.py, since Tag also references Lab via the same junction table.
from app.models.tag import Tag  # noqa: E402
