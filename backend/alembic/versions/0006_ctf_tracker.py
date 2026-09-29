"""add ctf tracker tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ctf_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("platform", sa.String(100), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ctf_events_user_id", "ctf_events", ["user_id"])

    op.create_table(
        "ctf_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ctf_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ctf_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="Unsolved"),
        sa.Column("time_spent_minutes", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("solution_writeup", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ctf_challenges_ctf_event_id", "ctf_challenges", ["ctf_event_id"])
    op.create_index("ix_ctf_challenges_category", "ctf_challenges", ["category"])
    op.create_index("ix_ctf_challenges_status", "ctf_challenges", ["status"])

    op.create_table(
        "ctf_challenge_skills",
        sa.Column("ctf_challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ctf_challenges.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "ctf_challenge_tools",
        sa.Column("ctf_challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ctf_challenges.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "ctf_challenge_techniques",
        sa.Column("ctf_challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ctf_challenges.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("technique_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("mitre_techniques.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "ctf_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ctf_challenge_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ctf_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(30), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(80), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ctf_evidence_ctf_challenge_id", "ctf_evidence", ["ctf_challenge_id"])


def downgrade() -> None:
    op.drop_index("ix_ctf_evidence_ctf_challenge_id", table_name="ctf_evidence")
    op.drop_table("ctf_evidence")
    op.drop_table("ctf_challenge_techniques")
    op.drop_table("ctf_challenge_tools")
    op.drop_table("ctf_challenge_skills")
    op.drop_index("ix_ctf_challenges_status", table_name="ctf_challenges")
    op.drop_index("ix_ctf_challenges_category", table_name="ctf_challenges")
    op.drop_index("ix_ctf_challenges_ctf_event_id", table_name="ctf_challenges")
    op.drop_table("ctf_challenges")
    op.drop_index("ix_ctf_events_user_id", table_name="ctf_events")
    op.drop_table("ctf_events")
