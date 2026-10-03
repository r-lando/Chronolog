import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.lab import Lab
from app.models.tag import Tag


def get_owned_lab_or_404(db: Session, lab_id: uuid.UUID, user_id: uuid.UUID) -> Lab:
    """
    Fetches a lab and enforces that it belongs to the requesting user.

    Returning 404 (not 403) when the lab exists but belongs to someone
    else avoids confirming to a caller that a given lab id exists at
    all — a small but real defense against ID enumeration.
    """
    lab = db.get(Lab, lab_id)
    if lab is None or lab.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
    return lab


def list_labs_for_user(
    db: Session,
    user_id: uuid.UUID,
    *,
    category: str | None = None,
    difficulty: str | None = None,
    status_filter: str | None = None,
    platform: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> list[Lab]:
    query = select(Lab).where(Lab.user_id == user_id)

    if category:
        query = query.where(Lab.category == category)
    if difficulty:
        query = query.where(Lab.difficulty == difficulty)
    if status_filter:
        query = query.where(Lab.status == status_filter)
    if platform:
        query = query.where(Lab.platform.ilike(f"%{platform}%"))
    if tag:
        query = query.join(Lab.tags).where(Tag.name.ilike(tag))
    if search:
        like_pattern = f"%{search}%"
        query = query.where(Lab.title.ilike(like_pattern) | Lab.description.ilike(like_pattern))

    query = query.order_by(Lab.updated_at.desc())
    return list(db.execute(query).scalars().unique().all())


def get_owned_evidence_or_404(db: Session, evidence_id: uuid.UUID, user_id: uuid.UUID) -> Evidence:
    """Same not-found-vs-forbidden reasoning as get_owned_lab_or_404, joined through the parent lab."""
    evidence = (
        db.query(Evidence)
        .join(Lab, Evidence.lab_id == Lab.id)
        .filter(Evidence.id == evidence_id, Lab.user_id == user_id)
        .first()
    )
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return evidence


def get_or_create_tag(db: Session, name: str) -> Tag:
    normalized = name.strip().lower()
    tag = db.query(Tag).filter(Tag.name == normalized).first()
    if tag is None:
        tag = Tag(name=normalized)
        db.add(tag)
        db.flush()
    return tag
