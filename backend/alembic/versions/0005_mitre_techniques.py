"""add mitre_techniques and lab_techniques

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mitre_techniques",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("technique_id", sa.String(20), nullable=False, unique=True),
        sa.Column("sub_technique_id", sa.String(20), nullable=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("tactic", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_mitre_techniques_technique_id", "mitre_techniques", ["technique_id"])
    op.create_index("ix_mitre_techniques_tactic", "mitre_techniques", ["tactic"])

    op.create_table(
        "lab_techniques",
        sa.Column("lab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "technique_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mitre_techniques.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("lab_techniques")
    op.drop_index("ix_mitre_techniques_tactic", table_name="mitre_techniques")
    op.drop_index("ix_mitre_techniques_technique_id", table_name="mitre_techniques")
    op.drop_table("mitre_techniques")
