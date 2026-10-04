import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import GUID
from app.models.mitre import MitreTechnique
from app.models.skill import Skill
from app.models.tool import Tool

# Plain many-to-many junctions, defined here (not in skill.py/tool.py) because
# the relationship only needs to be navigated from the CtfChallenge side —
# unlike Skill/Tool's relationship to Lab, nothing needs `skill.ctf_challenges`
# for stats purposes, so no back_populates and no circular import is needed.
ctf_challenge_skills = Table(
    "ctf_challenge_skills",
    Base.metadata,
    Column("ctf_challenge_id", GUID(), ForeignKey("ctf_challenges.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", GUID(), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

ctf_challenge_tools = Table(
    "ctf_challenge_tools",
    Base.metadata,
    Column("ctf_challenge_id", GUID(), ForeignKey("ctf_challenges.id", ondelete="CASCADE"), primary_key=True),
    Column("tool_id", GUID(), ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
)


class CtfEvent(Base):
    """A competition or platform session (e.g. 'PicoCTF 2026'), containing one or more challenges."""

    __tablename__ = "ctf_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    challenges: Mapped[list["CtfChallenge"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class CtfChallenge(Base):
    __tablename__ = "ctf_challenges"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ctf_event_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ctf_events.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Unsolved", index=True)
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_writeup: Mapped[str | None] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    event: Mapped["CtfEvent"] = relationship(back_populates="challenges")
    skills: Mapped[list["Skill"]] = relationship(secondary=ctf_challenge_skills)
    tools: Mapped[list["Tool"]] = relationship(secondary=ctf_challenge_tools)
    techniques: Mapped[list["CtfChallengeTechnique"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )
    evidence: Mapped[list["CtfEvidence"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class CtfChallengeTechnique(Base):
    """
    Association object mirroring LabTechnique — same required-justification
    guardrail against fabricated ATT&CK mappings applies here too.
    """

    __tablename__ = "ctf_challenge_techniques"

    ctf_challenge_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ctf_challenges.id", ondelete="CASCADE"), primary_key=True
    )
    technique_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("mitre_techniques.id", ondelete="CASCADE"), primary_key=True
    )
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    challenge: Mapped["CtfChallenge"] = relationship(back_populates="techniques")
    technique: Mapped["MitreTechnique"] = relationship()  # one-directional; no reverse list needed


class CtfEvidence(Base):
    """Same shape and same security handling as Evidence (see app/models/evidence.py), scoped to a CTF challenge."""

    __tablename__ = "ctf_evidence"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ctf_challenge_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ctf_challenges.id", ondelete="CASCADE"), nullable=False, index=True
    )

    evidence_type: Mapped[str] = mapped_column(String(30), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    challenge: Mapped["CtfChallenge"] = relationship(back_populates="evidence")
