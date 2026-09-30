import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ctf import CtfChallenge, CtfChallengeTechnique, CtfEvent, CtfEvidence


def get_owned_event_or_404(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> CtfEvent:
    event = db.get(CtfEvent, event_id)
    if event is None or event.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CTF event not found")
    return event


def get_owned_challenge_or_404(db: Session, challenge_id: uuid.UUID, user_id: uuid.UUID) -> CtfChallenge:
    challenge = (
        db.query(CtfChallenge)
        .join(CtfEvent, CtfChallenge.ctf_event_id == CtfEvent.id)
        .filter(CtfChallenge.id == challenge_id, CtfEvent.user_id == user_id)
        .first()
    )
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CTF challenge not found")
    return challenge


def get_owned_ctf_evidence_or_404(db: Session, evidence_id: uuid.UUID, user_id: uuid.UUID) -> CtfEvidence:
    evidence = (
        db.query(CtfEvidence)
        .join(CtfChallenge, CtfEvidence.ctf_challenge_id == CtfChallenge.id)
        .join(CtfEvent, CtfChallenge.ctf_event_id == CtfEvent.id)
        .filter(CtfEvidence.id == evidence_id, CtfEvent.user_id == user_id)
        .first()
    )
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return evidence


def get_challenge_technique_mapping(
    db: Session, challenge_id: uuid.UUID, technique_pk: uuid.UUID
) -> CtfChallengeTechnique | None:
    return (
        db.query(CtfChallengeTechnique)
        .filter(
            CtfChallengeTechnique.ctf_challenge_id == challenge_id,
            CtfChallengeTechnique.technique_id == technique_pk,
        )
        .first()
    )


def list_events_for_user(db: Session, user_id: uuid.UUID) -> list[CtfEvent]:
    return db.query(CtfEvent).filter(CtfEvent.user_id == user_id).order_by(CtfEvent.created_at.desc()).all()
