"""
Public portfolio endpoints.

Everything in this router is intentionally reachable without
authentication — that's the entire point of a public portfolio. The
safety boundary is not "require login", it's "only ever return data
that has gone through build_public_lab_view() or an equivalent explicit
allow-list" (see app/services/portfolio_service.py). No endpoint here
ever queries a Lab, Evidence, or write-up field directly and returns it
raw.

Rate limited (not auth-gated) to slow down scraping/enumeration, since
these routes are deliberately open to the internet.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.evidence import Evidence
from app.models.lab import Lab
from app.rate_limit import limiter
from app.schemas.portfolio import PublicLabOut, PublicLabSummaryOut
from app.services.evidence_service import resolve_evidence_path
from app.services.portfolio_service import build_lab_summary_view, build_public_lab_view, get_public_lab_by_slug, list_public_labs

router = APIRouter(prefix="/public", tags=["public-portfolio"])
settings = get_settings()


@router.get("/portfolio", response_model=list[PublicLabSummaryOut])
@limiter.limit(settings.rate_limit_public)
def list_portfolio(request: Request, db: Session = Depends(get_db)):
    return [build_lab_summary_view(lab) for lab in list_public_labs(db)]


@router.get("/portfolio/{slug}", response_model=PublicLabOut)
@limiter.limit(settings.rate_limit_public)
def get_portfolio_lab(slug: str, request: Request, db: Session = Depends(get_db)):
    lab = get_public_lab_by_slug(db, slug)
    if lab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This lab is not published.")
    return build_public_lab_view(db, lab)


@router.get("/evidence/{evidence_id}/file")
@limiter.limit(settings.rate_limit_public)
def get_public_evidence_file(evidence_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """
    Serves an evidence file only if BOTH are true: the evidence row is
    marked is_public, and its parent lab is currently portfolio-ready.
    Checking the lab's current status (not just the evidence flag) means
    unpublishing a lab immediately cuts off its evidence files too, even
    if someone saved a direct link earlier.
    """
    evidence = (
        db.query(Evidence)
        .join(Lab, Evidence.lab_id == Lab.id)
        .filter(Evidence.id == evidence_id, Evidence.is_public.is_(True), Lab.is_portfolio_ready.is_(True))
        .first()
    )
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    path = resolve_evidence_path(evidence.stored_filename, settings)
    return FileResponse(
        path=path,
        media_type=evidence.mime_type,
        filename=evidence.original_filename,
        content_disposition_type="attachment",
    )
