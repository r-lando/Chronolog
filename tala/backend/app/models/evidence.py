import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID


class Evidence(Base):
    """
    Metadata for one uploaded evidence file. The actual bytes are never
    stored in the database — only in EVIDENCE_STORAGE_PATH under
    `stored_filename`, a server-generated name with no relationship to
    anything the uploader typed (see app/services/evidence_service.py).

    `original_filename` is kept purely for display; it is sanitized
    (basename only) before storage and is NEVER used to build a
    filesystem path.
    """

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lab_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("findings.id", ondelete="SET NULL"), nullable=True
    )

    evidence_type: Mapped[str] = mapped_column(String(30), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Governs Milestone 9 portfolio exposure only — never used to bypass
    # authentication in this milestone's own /evidence/{id}/file route.
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    finding: Mapped["Finding"] = relationship(back_populates="evidence")


# Imported at the bottom to resolve the "Finding" forward reference above
# without a circular-import failure, mirroring the pattern in lab.py/tag.py.
from app.models.finding import Finding  # noqa: E402
