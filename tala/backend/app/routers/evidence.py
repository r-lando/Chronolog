"""
Findings and evidence endpoints.

Every route is authenticated and every lab/evidence lookup is scoped to
the requesting user (see app/services/lab_service.py). The upload route
additionally goes through app/services/evidence_service.py for
extension whitelisting, content validation, size enforcement, and safe
storage — see that module's docstring for the full rationale.

Evidence is downloaded through GET /evidence/{id}/file rather than a
static file server, so every download re-checks ownership at request
time and the file is always served with Content-Disposition: attachment
(never "inline"), which stops a browser from executing or rendering an
evidence file's contents (e.g. an uploaded .log that happens to contain
HTML/script) in the context of this application's origin.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.audit import record_audit_event
from app.config import get_settings
from app.constants import EVIDENCE_TYPES
from app.database import get_db
from app.dependencies import get_current_user
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.evidence import EvidenceOut, EvidenceUpdate, EvidenceWithLabOut
from app.schemas.finding import FindingCreate, FindingOut
from app.services.evidence_service import delete_evidence_file, resolve_evidence_path, validate_and_store_upload
from app.services.lab_service import get_owned_evidence_or_404, get_owned_lab_or_404

router = APIRouter(tags=["evidence"])
settings = get_settings()


def _get_owned_finding_or_404(db: Session, finding_id: uuid.UUID, user_id: uuid.UUID) -> Finding:
    """Ownership check for a finding, joined through its parent lab."""
    from app.models.lab import Lab

    finding = (
        db.query(Finding)
        .join(Lab, Finding.lab_id == Lab.id)
        .filter(Finding.id == finding_id, Lab.user_id == user_id)
        .first()
    )
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding


@router.get("/evidence", response_model=list[EvidenceWithLabOut])
def list_all_evidence(
    evidence_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All evidence across every lab owned by the current user — backs the top-level Evidence page."""
    from app.models.lab import Lab

    query = db.query(Evidence, Lab.title).join(Lab, Evidence.lab_id == Lab.id).filter(Lab.user_id == current_user.id)
    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)
    query = query.order_by(Evidence.uploaded_at.desc())

    results = []
    for evidence, lab_title in query.all():
        base_fields = EvidenceOut.model_validate(evidence).model_dump()
        results.append(EvidenceWithLabOut(**base_fields, lab_title=lab_title))
    return results


# ---- Findings ---------------------------------------------------------


@router.post("/labs/{lab_id}/findings", response_model=FindingOut, status_code=status.HTTP_201_CREATED)
def create_finding(
    lab_id: uuid.UUID,
    payload: FindingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    finding = Finding(lab_id=lab.id, **payload.model_dump())
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


@router.get("/labs/{lab_id}/findings", response_model=list[FindingOut])
def list_findings(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    return db.query(Finding).filter(Finding.lab_id == lab.id).order_by(Finding.created_at.desc()).all()


@router.delete("/findings/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finding(
    finding_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    finding = _get_owned_finding_or_404(db, finding_id, current_user.id)
    db.delete(finding)  # evidence.finding_id is ON DELETE SET NULL — evidence itself is preserved
    db.commit()


# ---- Evidence -----------------------------------------------------------


@router.post("/labs/{lab_id}/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_upload)
async def upload_evidence(
    request: Request,
    lab_id: uuid.UUID,
    evidence_type: str = Form(...),
    description: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    finding_id: uuid.UUID | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)

    if evidence_type not in EVIDENCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"evidence_type must be one of: {', '.join(EVIDENCE_TYPES)}",
        )

    if finding_id is not None:
        finding = db.query(Finding).filter(Finding.id == finding_id, Finding.lab_id == lab.id).first()
        if finding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="finding_id does not belong to this lab"
            )

    validated = await validate_and_store_upload(file, settings)

    evidence = Evidence(
        lab_id=lab.id,
        finding_id=finding_id,
        evidence_type=evidence_type,
        original_filename=validated.original_filename,
        stored_filename=validated.stored_filename,
        mime_type=validated.mime_type,
        file_size_bytes=validated.file_size_bytes,
        sha256_hash=validated.sha256_hash,
        description=description,
        notes=notes,
    )
    db.add(evidence)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="evidence.upload",
        resource_type="evidence",
        resource_id=evidence.id,
        extra_data={
            "lab_id": str(lab.id),
            "sha256": validated.sha256_hash,
            "size_bytes": validated.file_size_bytes,
        },
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/labs/{lab_id}/evidence", response_model=list[EvidenceOut])
def list_evidence(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    return db.query(Evidence).filter(Evidence.lab_id == lab.id).order_by(Evidence.uploaded_at.desc()).all()


@router.get("/evidence/{evidence_id}/file")
def download_evidence_file(
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = get_owned_evidence_or_404(db, evidence_id, current_user.id)
    path = resolve_evidence_path(evidence.stored_filename, settings)

    return FileResponse(
        path=path,
        media_type=evidence.mime_type,
        filename=evidence.original_filename,
        content_disposition_type="attachment",
    )


@router.patch("/evidence/{evidence_id}", response_model=EvidenceOut)
def update_evidence(
    evidence_id: uuid.UUID,
    payload: EvidenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = get_owned_evidence_or_404(db, evidence_id, current_user.id)

    if payload.finding_id is not None:
        finding_exists = (
            db.query(Finding)
            .filter(Finding.id == payload.finding_id, Finding.lab_id == evidence.lab_id)
            .first()
        )
        if finding_exists is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="finding_id does not belong to this lab"
            )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(evidence, field, value)

    db.commit()
    db.refresh(evidence)
    return evidence


@router.delete("/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    evidence_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = get_owned_evidence_or_404(db, evidence_id, current_user.id)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="evidence.delete",
        resource_type="evidence",
        resource_id=evidence.id,
        ip_address=request.client.host if request.client else None,
    )
    delete_evidence_file(evidence.stored_filename, settings)
    db.delete(evidence)
    db.commit()
