import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID


class Finding(Base):
    """
    A discrete, structured observation within a lab — distinct from the
    free-text "Findings" section of the write-up. Splitting this out
    lets evidence point at a specific finding ("this screenshot proves
    this finding") rather than only at the lab as a whole.
    """

    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lab_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    evidence: Mapped[list["Evidence"]] = relationship(back_populates="finding")


# Imported at the bottom to resolve the "Evidence" forward reference above
# without a circular-import failure, mirroring the pattern in lab.py/tag.py.
from app.models.evidence import Evidence  # noqa: E402
