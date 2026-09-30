"""add skills, tools, lab_skills, lab_tools

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
    )
    op.create_index("ix_skills_name", "skills", ["name"])

    op.create_table(
        "tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
    )
    op.create_index("ix_tools_name", "tools", ["name"])

    op.create_table(
        "lab_skills",
        sa.Column("lab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "lab_tools",
        sa.Column("lab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("lab_tools")
    op.drop_table("lab_skills")
    op.drop_index("ix_tools_name", table_name="tools")
    op.drop_table("tools")
    op.drop_index("ix_skills_name", table_name="skills")
    op.drop_table("skills")
