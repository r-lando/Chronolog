"""
CTF tracker endpoints.

Mirrors the Labs + Evidence routers' patterns deliberately: same
ownership-check style (404, not 403, for another user's resource), same
evidence upload security pipeline (app/services/evidence_service.py is
fully lab-agnostic — it only needs a file and settings), and the same
required-justification guardrail for MITRE technique mappings.

Per the product spec, this app does not solve CTF challenges or reveal
external solutions — solution_writeup is a field the user fills in
themselves after solving a challenge on their own.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.audit import record_audit_event
from app.config import get_settings
from app.constants import CTF_CATEGORIES, CTF_STATUSES, EVIDENCE_TYPES, LAB_DIFFICULTIES
from app.database import get_db
from app.dependencies import get_current_user
from app.models.ctf import CtfChallenge, CtfChallengeTechnique, CtfEvent, CtfEvidence
from app.models.mitre import MitreTechnique
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.common import NameAttach
from app.schemas.ctf import (
    CtfChallengeCreate,
    CtfChallengeOut,
    CtfChallengeTechniqueAttach,
    CtfChallengeUpdate,
    CtfEventCreate,
    CtfEventDetailOut,
    CtfEventOut,
    CtfOptionsOut,
)
from app.schemas.ctf_evidence import CtfEvidenceOut, CtfEvidenceUpdate
from app.schemas.mitre import LabTechniqueOut
from app.schemas.skill import SkillOut
from app.schemas.tool import ToolOut
from app.services.ctf_service import (
    get_challenge_technique_mapping,
    get_owned_challenge_or_404,
    get_owned_ctf_evidence_or_404,
    get_owned_event_or_404,
    list_events_for_user,
)
from app.services.evidence_service import delete_evidence_file, resolve_evidence_path, validate_and_store_upload
from app.services.skill_tool_service import get_or_create_skill, get_or_create_tool

router = APIRouter(tags=["ctf"])
settings = get_settings()


@router.get("/ctf-options", response_model=CtfOptionsOut)
def get_ctf_options():
    return CtfOptionsOut(categories=CTF_CATEGORIES, difficulties=LAB_DIFFICULTIES, statuses=CTF_STATUSES)


# ---- CTF Events -----------------------------------------------------------


@router.get("/ctf-events", response_model=list[CtfEventOut])
def list_ctf_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_events_for_user(db, current_user.id)


@router.post("/ctf-events", response_model=CtfEventOut, status_code=status.HTTP_201_CREATED)
def create_ctf_event(
    payload: CtfEventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    event = CtfEvent(user_id=current_user.id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/ctf-events/{event_id}", response_model=CtfEventDetailOut)
def get_ctf_event(
    event_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return get_owned_event_or_404(db, event_id, current_user.id)


@router.put("/ctf-events/{event_id}", response_model=CtfEventOut)
def update_ctf_event(
    event_id: uuid.UUID,
    payload: CtfEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = get_owned_event_or_404(db, event_id, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/ctf-events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ctf_event(
    event_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = get_owned_event_or_404(db, event_id, current_user.id)

    # Same reasoning as lab deletion: clean up evidence files from disk
    # before the DB cascade removes the challenge/evidence rows, since
    # the database cascade has no way to touch the filesystem.
    evidence_records = (
        db.query(CtfEvidence)
        .join(CtfChallenge, CtfEvidence.ctf_challenge_id == CtfChallenge.id)
        .filter(CtfChallenge.ctf_event_id == event.id)
        .all()
    )
    for evidence in evidence_records:
        delete_evidence_file(evidence.stored_filename, settings)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="ctf_event.delete",
        resource_type="ctf_event",
        resource_id=event.id,
        ip_address=request.client.host if request.client else None,
    )
    db.delete(event)
    db.commit()


# ---- CTF Challenges ---------------------------------------------------


@router.post(
    "/ctf-events/{event_id}/challenges", response_model=CtfChallengeOut, status_code=status.HTTP_201_CREATED
)
def create_ctf_challenge(
    event_id: uuid.UUID,
    payload: CtfChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = get_owned_event_or_404(db, event_id, current_user.id)
    challenge = CtfChallenge(ctf_event_id=event.id, **payload.model_dump())
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("/ctf-events/{event_id}/challenges", response_model=list[CtfChallengeOut])
def list_ctf_challenges(
    event_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    event = get_owned_event_or_404(db, event_id, current_user.id)
    return event.challenges


@router.get("/ctf-challenges/{challenge_id}", response_model=CtfChallengeOut)
def get_ctf_challenge(
    challenge_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return get_owned_challenge_or_404(db, challenge_id, current_user.id)


@router.put("/ctf-challenges/{challenge_id}", response_model=CtfChallengeOut)
def update_ctf_challenge(
    challenge_id: uuid.UUID,
    payload: CtfChallengeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(challenge, field, value)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.delete("/ctf-challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ctf_challenge(
    challenge_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)

    for evidence in challenge.evidence:
        delete_evidence_file(evidence.stored_filename, settings)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="ctf_challenge.delete",
        resource_type="ctf_challenge",
        resource_id=challenge.id,
        ip_address=request.client.host if request.client else None,
    )
    db.delete(challenge)
    db.commit()


# ---- Skills / Tools / Techniques on a challenge ------------------------


@router.post("/ctf-challenges/{challenge_id}/skills", response_model=list[SkillOut])
def add_challenge_skill(
    challenge_id: uuid.UUID,
    payload: NameAttach,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)
    skill = get_or_create_skill(db, payload.name)
    if skill not in challenge.skills:
        challenge.skills.append(skill)
    db.commit()
    db.refresh(challenge)
    return challenge.skills


@router.delete("/ctf-challenges/{challenge_id}/skills/{skill_id}", response_model=list[SkillOut])
def remove_challenge_skill(
    challenge_id: uuid.UUID,
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)
    challenge.skills = [s for s in challenge.skills if s.id != skill_id]
    db.commit()
    db.refresh(challenge)
    return challenge.skills


@router.post("/ctf-challenges/{challenge_id}/tools", response_model=list[ToolOut])
def add_challenge_tool(
    challenge_id: uuid.UUID,
    payload: NameAttach,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)
    tool = get_or_create_tool(db, payload.name)
    if tool not in challenge.tools:
        challenge.tools.append(tool)
    db.commit()
    db.refresh(challenge)
    return challenge.tools


@router.delete("/ctf-challenges/{challenge_id}/tools/{tool_id}", response_model=list[ToolOut])
def remove_challenge_tool(
    challenge_id: uuid.UUID,
    tool_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)
    challenge.tools = [t for t in challenge.tools if t.id != tool_id]
    db.commit()
    db.refresh(challenge)
    return challenge.tools


@router.post("/ctf-challenges/{challenge_id}/techniques", response_model=list[LabTechniqueOut])
def add_challenge_technique(
    challenge_id: uuid.UUID,
    payload: CtfChallengeTechniqueAttach,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)

    technique = db.get(MitreTechnique, payload.technique_id)
    if technique is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown MITRE technique. Only techniques from the reference list can be mapped.",
        )

    existing = get_challenge_technique_mapping(db, challenge.id, technique.id)
    if existing is not None:
        existing.justification = payload.justification
    else:
        db.add(
            CtfChallengeTechnique(
                ctf_challenge_id=challenge.id, technique_id=technique.id, justification=payload.justification
            )
        )

    db.commit()
    db.refresh(challenge)
    return challenge.techniques


@router.delete("/ctf-challenges/{challenge_id}/techniques/{technique_id}", response_model=list[LabTechniqueOut])
def remove_challenge_technique(
    challenge_id: uuid.UUID,
    technique_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)
    mapping = get_challenge_technique_mapping(db, challenge.id, technique_id)
    if mapping is not None:
        db.delete(mapping)
        db.commit()
        db.refresh(challenge)
    return challenge.techniques


# ---- CTF Evidence -------------------------------------------------------


@router.post(
    "/ctf-challenges/{challenge_id}/evidence", response_model=CtfEvidenceOut, status_code=status.HTTP_201_CREATED
)
@limiter.limit(settings.rate_limit_upload)
async def upload_ctf_evidence(
    request: Request,
    challenge_id: uuid.UUID,
    evidence_type: str = Form(...),
    description: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)

    if evidence_type not in EVIDENCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"evidence_type must be one of: {', '.join(EVIDENCE_TYPES)}",
        )

    validated = await validate_and_store_upload(file, settings)

    evidence = CtfEvidence(
        ctf_challenge_id=challenge.id,
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
        action="ctf_evidence.upload",
        resource_type="ctf_evidence",
        resource_id=evidence.id,
        extra_data={"ctf_challenge_id": str(challenge.id), "sha256": validated.sha256_hash},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/ctf-challenges/{challenge_id}/evidence", response_model=list[CtfEvidenceOut])
def list_ctf_evidence(
    challenge_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    challenge = get_owned_challenge_or_404(db, challenge_id, current_user.id)
    return challenge.evidence


@router.get("/ctf-evidence/{evidence_id}/file")
def download_ctf_evidence_file(
    evidence_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    evidence = get_owned_ctf_evidence_or_404(db, evidence_id, current_user.id)
    path = resolve_evidence_path(evidence.stored_filename, settings)
    return FileResponse(
        path=path, media_type=evidence.mime_type, filename=evidence.original_filename, content_disposition_type="attachment"
    )


@router.patch("/ctf-evidence/{evidence_id}", response_model=CtfEvidenceOut)
def update_ctf_evidence(
    evidence_id: uuid.UUID,
    payload: CtfEvidenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = get_owned_ctf_evidence_or_404(db, evidence_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(evidence, field, value)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.delete("/ctf-evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ctf_evidence(
    evidence_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = get_owned_ctf_evidence_or_404(db, evidence_id, current_user.id)

    record_audit_event(
        db,
        user_id=current_user.id,
        action="ctf_evidence.delete",
        resource_type="ctf_evidence",
        resource_id=evidence.id,
        ip_address=request.client.host if request.client else None,
    )
    delete_evidence_file(evidence.stored_filename, settings)
    db.delete(evidence)
    db.commit()
