import re
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.lab_service import get_owned_lab_or_404
from app.services.report_service import build_lab_report_context, build_learning_summary_context, render_report

router = APIRouter(tags=["reports"])
settings = get_settings()

_MEDIA_TYPES = {"pdf": "application/pdf", "markdown": "text/markdown"}
_EXTENSIONS = {"pdf": "pdf", "markdown": "md"}


def _validate_format(fmt: str) -> None:
    if fmt not in _MEDIA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="format must be 'pdf' or 'markdown'"
        )


def _safe_filename_stem(text: str) -> str:
    """Strips anything but letters/digits/hyphens so the result is always safe inside a Content-Disposition header."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "report"


def _attachment_response(content: bytes, fmt: str, filename_stem: str) -> Response:
    return Response(
        content=content,
        media_type=_MEDIA_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename_stem}.{_EXTENSIONS[fmt]}"'},
    )


@router.get("/labs/{lab_id}/report")
def get_lab_report(
    lab_id: uuid.UUID,
    format: str = Query(default="markdown"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_format(format)
    lab = get_owned_lab_or_404(db, lab_id, current_user.id)
    context = build_lab_report_context(db, lab, settings)
    content = render_report("lab_report", context, format)

    slug_source = lab.portfolio_slug or _safe_filename_stem(lab.title)
    return _attachment_response(content, format, f"lab-report-{slug_source}")


@router.get("/reports/learning-summary")
def get_learning_summary(
    format: str = Query(default="markdown"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_format(format)
    context = build_learning_summary_context(db, current_user.id, date.today())
    content = render_report("learning_summary", context, format)
    return _attachment_response(content, format, "learning-summary")
