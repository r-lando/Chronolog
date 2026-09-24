"""
Import every model module here so that Base.metadata is fully populated
for Alembic autogenerate and for Base.metadata.create_all in tests.
As new tables are added in later milestones, import them here too.
"""

from app.models.user import User  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
