import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    *,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    extra_data: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Writes one audit log entry. Callers are responsible for committing
    (usually as part of the same transaction as the action itself) so a
    failed audit write can't silently let an unlogged action through.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        extra_data=extra_data,
        ip_address=ip_address,
    )
    db.add(entry)
