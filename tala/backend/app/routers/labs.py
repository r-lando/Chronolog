"""
Lab management endpoints.

Every route here requires authentication (get_current_user) and every
lookup by id goes through get_owned_lab_or_404, so a user can never
read, edit, or delete a lab that isn't theirs — even though this is a
single-user deployment today, the authorization check costs nothing
and keeps the schema honest for any future multi-user use.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.audit import record_audit_event
from app.config import get_settings
from app.constants import LAB_CATEGORIES, LAB_DIFFICULTIES, LAB_STATUSES
from app.database import get_db
from app.dependencies import get_current_user
from app.models.evidence import Evidence
from app.models.lab import Lab, LabWriteup
from app.models.user import User
from app.schemas.lab import (
    LabCreate,
    LabDetailOut,
    LabOptionsOut,
    LabOut,
    LabStatusUpdate,
    LabUpdate,
    LabWriteupOut,
    LabWriteupUpdate,
    TagAttach,
    TagOut,
)
from app.services.evidence_service import delete_evidence_file
from app.services.lab_service import get_or_create_tag, get_owned_lab_or_404, list_labs_for_user

router = APIRouter(prefix="/labs", tags=["labs"])
settings = get_settings()


@router.get("/options", response_model=LabOptionsOut)
def get_lab_options():
    """Lets the frontend build dropdowns from the same list the backend validates against."""
    return LabOptionsOut(categories=LAB_CATEGORIES, difficulties=LAB_DIFFICULTIES, statuses=LAB_STATUSES)


@router.get("", response_model=list[LabOut])
def list_labs(
    category: str | None = None,
    difficulty: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_labs_for_user(
        db,
        current_user.id,
        category=category,
        difficulty=difficulty,
        status_filter=status,
        platform=platform,
        tag=tag,
        search=search,
    )


@router.post("", response_model=LabDetailOut, status_code=status.HTTP_201_CREATED)
def create_lab(
    request: Request,
    payload: LabCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = Lab(user_id=current_user.id, **payload.model_dump())
    db.add(lab)
    db.flush()

    # Every lab gets an empty write-up shell immediately so the frontend
    # can always PUT to /labs/{id}/writeup without a "does it exist yet"
    # branch.
    writeup = LabWriteup(lab_id=lab.id)
    db.add(writeup)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="lab.create",
        resource_type="lab",
        resource_id=lab.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(lab)
    return lab


@router.get("/{lab_id}", response_model=LabDetailOut)
def get_lab(lab_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_owned_lab_or_404(db, lab_id, current_user.id)


@router.put("/{lab_id}", response_model=LabDetailOut)
def update_lab(
    lab_id: uuid.UUID,
    payload: LabUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(lab, field, value)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="lab.update",
        resource_type="lab",
        resource_id=lab.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(lab)
    return lab


@router.patch("/{lab_id}/status", response_model=LabOut)
def update_lab_status(
    lab_id: uuid.UUID,
    payload: LabStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    lab.status = payload.status

    record_audit_event(
        db,
        user_id=current_user.id,
        action="lab.status_change",
        resource_type="lab",
        resource_id=lab.id,
        extra_data={"new_status": payload.status},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(lab)
    return lab


@router.delete("/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab(
    lab_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)

    # Evidence rows cascade-delete at the database level (ON DELETE
    # CASCADE), but the physical files on disk don't — the database has
    # no way to touch the filesystem. Clean those up explicitly first,
    # or every lab deletion would silently leak evidence files forever.
    evidence_records = db.query(Evidence).filter(Evidence.lab_id == lab.id).all()
    for evidence in evidence_records:
        delete_evidence_file(evidence.stored_filename, settings)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="lab.delete",
        resource_type="lab",
        resource_id=lab.id,
        extra_data={"evidence_files_removed": len(evidence_records)},
        ip_address=request.client.host if request.client else None,
    )
    db.delete(lab)  # cascades to writeup (ORM), and to evidence/findings (DB-level FK cascade)
    db.commit()


@router.put("/{lab_id}/writeup", response_model=LabWriteupOut)
def update_writeup(
    lab_id: uuid.UUID,
    payload: LabWriteupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    if lab.writeup is None:
        lab.writeup = LabWriteup(lab_id=lab.id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lab.writeup, field, value)

    db.commit()
    db.refresh(lab.writeup)
    return lab.writeup


@router.post("/{lab_id}/tags", response_model=list[TagOut])
def add_tag(
    lab_id: uuid.UUID,
    payload: TagAttach,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    tag = get_or_create_tag(db, payload.name)
    if tag not in lab.tags:
        lab.tags.append(tag)
    db.commit()
    db.refresh(lab)
    return lab.tags


@router.delete("/{lab_id}/tags/{tag_id}", response_model=list[TagOut])
def remove_tag(
    lab_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    lab.tags = [t for t in lab.tags if t.id != tag_id]
    db.commit()
    db.refresh(lab)
    return lab.tags
