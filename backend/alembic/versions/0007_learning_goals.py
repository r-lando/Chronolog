"""add learning_goals

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "parent_goal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("learning_goals.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("related_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_learning_goals_user_id", "learning_goals", ["user_id"])
    op.create_index("ix_learning_goals_parent_goal_id", "learning_goals", ["parent_goal_id"])


def downgrade() -> None:
    op.drop_index("ix_learning_goals_parent_goal_id", table_name="learning_goals")
    op.drop_index("ix_learning_goals_user_id", table_name="learning_goals")
    op.drop_table("learning_goals")
