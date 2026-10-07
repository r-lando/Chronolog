"""add labs, lab_writeups, tags, lab_tags

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("platform", sa.String(100), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="Planned"),
        sa.Column("date_started", sa.Date(), nullable=True),
        sa.Column("date_completed", sa.Date(), nullable=True),
        sa.Column("time_spent_minutes", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("environment", sa.Text(), nullable=True),
        sa.Column("is_portfolio_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("portfolio_slug", sa.String(220), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_labs_user_id", "labs", ["user_id"])
    op.create_index("ix_labs_category", "labs", ["category"])
    op.create_index("ix_labs_difficulty", "labs", ["difficulty"])
    op.create_index("ix_labs_status", "labs", ["status"])

    op.create_table(
        "lab_writeups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("methodology", sa.Text(), nullable=True),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("reflection", sa.Text(), nullable=True),
        sa.Column("next_steps", sa.Text(), nullable=True),
        sa.Column("format", sa.String(20), nullable=False, server_default="markdown"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
    )
    op.create_index("ix_tags_name", "tags", ["name"])

    op.create_table(
        "lab_tags",
        sa.Column("lab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("lab_tags")
    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_table("tags")
    op.drop_table("lab_writeups")
    op.drop_index("ix_labs_status", table_name="labs")
    op.drop_index("ix_labs_difficulty", table_name="labs")
    op.drop_index("ix_labs_category", table_name="labs")
    op.drop_index("ix_labs_user_id", table_name="labs")
    op.drop_table("labs")
