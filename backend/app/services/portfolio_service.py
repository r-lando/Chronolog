"""
Portfolio publishing and the public-view sanitization boundary.

Every exclusion the product spec requires is enforced in exactly one
place — build_public_lab_view() below — so there's a single function to
audit for "does this leak anything private":

- Evidence is included only if explicitly marked is_public=True. The
  default for new evidence is False (set in Milestone 3), so publishing
  a lab never retroactively exposes files the user didn't opt in.
- Evidence's `notes` field (private annotations) is never included,
  even for public evidence — only `description` is shown.
- The write-up's `reflection` field is never included on the public
  page at all, published or not. It's the field most likely to hold
  candid, non-portfolio-appropriate content ("this took me forever",
  mistakes made, frustration) and the spec's own list of public fields
  doesn't mention it.
- TALA cannot automatically detect secrets or credentials typed into
  free-text fields (write-up, descriptions, justifications) — that
  remains the user's responsibility. The UI warns about this before
  publishing (see the frontend's portfolio toggle confirmation).
"""

import re
import uuid

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.evidence import Evidence
from app.models.lab import Lab

settings = get_settings()

_SLUG_SAFE_CHARS = re.compile(r"[^a-z0-9]+")


def _slug_base(title: str) -> str:
    base = _SLUG_SAFE_CHARS.sub("-", title.lower()).strip("-")[:60]
    return base or "lab"


def generate_unique_slug(db: Session, title: str) -> str:
    """
    A random 8-hex-character suffix makes the slug both URL-friendly and
    non-enumerable — someone can't guess other labs' slugs by walking
    through sequential IDs or titles. Collisions are astronomically
    unlikely (16^8 possibilities) but checked anyway rather than assumed.
    """
    for _ in range(5):
        candidate = f"{_slug_base(title)}-{uuid.uuid4().hex[:8]}"
        if db.query(Lab).filter(Lab.portfolio_slug == candidate).first() is None:
            return candidate
    # Practically unreachable, but fail loudly rather than return a
    # possibly-colliding slug if we somehow exhaust the retry budget.
    raise RuntimeError("Could not generate a unique portfolio slug")


def list_public_labs(db: Session) -> list[Lab]:
    return db.query(Lab).filter(Lab.is_portfolio_ready.is_(True)).order_by(Lab.updated_at.desc()).all()


def get_public_lab_by_slug(db: Session, slug: str) -> Lab | None:
    return db.query(Lab).filter(Lab.portfolio_slug == slug, Lab.is_portfolio_ready.is_(True)).first()


def build_lab_summary_view(lab: Lab) -> dict:
    return {
        "slug": lab.portfolio_slug,
        "title": lab.title,
        "category": lab.category,
        "difficulty": lab.difficulty,
        "platform": lab.platform,
        "summary": lab.description,
        "published_at": lab.updated_at,
    }


def build_public_lab_view(db: Session, lab: Lab) -> dict:
    writeup = lab.writeup

    public_evidence = (
        db.query(Evidence).filter(Evidence.lab_id == lab.id, Evidence.is_public.is_(True)).all()
    )

    return {
        "slug": lab.portfolio_slug,
        "title": lab.title,
        "category": lab.category,
        "difficulty": lab.difficulty,
        "platform": lab.platform,
        "summary": lab.description,
        "objective": lab.objective,
        "environment": lab.environment,
        "methodology": writeup.methodology if writeup else None,
        "findings": writeup.findings if writeup else None,
        "analysis": writeup.analysis if writeup else None,
        "lessons_learned": writeup.lessons_learned if writeup else None,
        "next_steps": writeup.next_steps if writeup else None,
        # reflection is intentionally omitted — see module docstring
        "skills": [skill.name for skill in lab.skills],
        "tools": [tool.name for tool in lab.tools],
        "techniques": [
            {
                "technique_id": lt.technique.technique_id,
                "sub_technique_id": lt.technique.sub_technique_id,
                "name": lt.technique.name,
                "tactic": lt.technique.tactic,
                "justification": lt.justification,
            }
            for lt in lab.techniques
        ],
        "evidence": [
            {
                "id": str(evidence.id),
                "evidence_type": evidence.evidence_type,
                "original_filename": evidence.original_filename,
                "description": evidence.description,
                # notes is intentionally omitted — see module docstring
                "file_url": f"/api/v1/public/evidence/{evidence.id}/file",
            }
            for evidence in public_evidence
        ],
        "published_at": lab.updated_at,
    }
