import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID
from app.models.skill import Skill


class LearningGoal(Base):
    """
    One node in a learning roadmap tree, e.g.:

        SOC Analyst                  (parent_goal_id = None, related_skill_id = None)
        ├── Networking               (parent_goal_id = SOC Analyst's id, related_skill_id = None)
        ├── SIEM                     (parent_goal_id = SOC Analyst's id, related_skill_id = <SIEM skill>)
        └── Incident Response        (parent_goal_id = SOC Analyst's id, related_skill_id = <IR skill>)

    A goal only gets computed progress (labs completed, related CTFs, a
    recommended next activity) when it's linked to a real Skill — a
    grouping node like "SOC Analyst" is just organizational and shows a
    simple rollup of its children instead (see app/services/roadmap_service.py).
    """

    __tablename__ = "learning_goals"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_goal_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("learning_goals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    related_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    target_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    children: Mapped[list["LearningGoal"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped["LearningGoal | None"] = relationship(back_populates="children", remote_side=[id])
    related_skill: Mapped["Skill | None"] = relationship()
