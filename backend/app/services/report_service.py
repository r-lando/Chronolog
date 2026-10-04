"""
Report generation: Lab Report and Learning Summary, each as Markdown or PDF.

Design notes:

- Reports generated here are a PRIVATE export for the lab's owner, not a
  public artifact — unlike the portfolio (Milestone 9), a report
  includes everything: the Reflection field, every evidence file
  (public or private), and private notes are still excluded only
  because notes were never meant to be read by anyone, including in a
  report the user might hand to someone else. Reflection IS included
  here, deliberately, since this is the user's own document to do with
  as they choose — the sanitization boundary in portfolio_service.py
  governs automatic public exposure, not manual, deliberate sharing.
- The PDF and Markdown exports are built from two Jinja2 templates per
  report (one .html.jinja2, one .md.jinja2) sharing the same context
  dict, so both formats always show the same information.
- Write-up fields are stored as raw Markdown. For the PDF, each field
  is converted to HTML via the `markdown` library before being dropped
  into the HTML template (marked `| safe` there) — otherwise the PDF
  would show literal asterisks and pound signs instead of formatting.
  The Markdown export needs no conversion since the source is already
  Markdown.
- Only image evidence is embedded inline (as a base64 data URI, which
  WeasyPrint renders natively with no extra config) since that's the
  only evidence type where inline display meaningfully helps a reader.
  Everything else (logs, PCAPs, configs, reports) is listed in a
  reference table with its filename, type, description, and SHA-256
  hash instead of attempting to render arbitrary binary content.
"""

import base64
from datetime import date, datetime, timezone
from pathlib import Path

import markdown as markdown_lib
import weasyprint
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.lab import Lab
from app.services import stats_service
from app.services.evidence_service import resolve_evidence_path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "reports"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html.jinja2",)),
)


def _md_to_html(text: str | None) -> str:
    if not text:
        return ""
    return markdown_lib.markdown(text, extensions=["extra", "sane_lists"])


def _generated_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ---- Lab report -------------------------------------------------------------


def _build_evidence_sections(db: Session, lab: Lab, settings: Settings) -> tuple[list[dict], list[dict]]:
    """Splits a lab's evidence into inline-embeddable images and a reference table for everything else."""
    all_evidence = db.query(Evidence).filter(Evidence.lab_id == lab.id).all()

    image_evidence = []
    file_evidence = []
    for item in all_evidence:
        if item.mime_type.startswith("image/"):
            try:
                path = resolve_evidence_path(item.stored_filename, settings)
                data = Path(path).read_bytes()
                data_uri = f"data:{item.mime_type};base64,{base64.b64encode(data).decode('ascii')}"
                image_evidence.append(
                    {"filename": item.original_filename, "description": item.description, "data_uri": data_uri}
                )
                continue
            except Exception:
                pass  # file missing on disk for some reason — fall through to the reference-table listing below

        file_evidence.append(
            {
                "filename": item.original_filename,
                "evidence_type": item.evidence_type,
                "description": item.description,
                "sha256": item.sha256_hash,
            }
        )

    return image_evidence, file_evidence


def build_lab_report_context(db: Session, lab: Lab, settings: Settings) -> dict:
    writeup = lab.writeup
    structured_findings = db.query(Finding).filter(Finding.lab_id == lab.id).all()
    image_evidence, file_evidence = _build_evidence_sections(db, lab, settings)

    return {
        "title": lab.title,
        "category": lab.category,
        "difficulty": lab.difficulty,
        "status": lab.status,
        "platform": lab.platform,
        "date_started": lab.date_started.isoformat() if lab.date_started else None,
        "date_completed": lab.date_completed.isoformat() if lab.date_completed else None,
        "time_spent_minutes": lab.time_spent_minutes,
        "objective": lab.objective,
        "objective_html": _md_to_html(lab.objective),
        "environment": lab.environment,
        "environment_html": _md_to_html(lab.environment),
        "methodology": writeup.methodology if writeup else None,
        "methodology_html": _md_to_html(writeup.methodology if writeup else None),
        "findings": writeup.findings if writeup else None,
        "findings_html": _md_to_html(writeup.findings if writeup else None),
        "analysis": writeup.analysis if writeup else None,
        "analysis_html": _md_to_html(writeup.analysis if writeup else None),
        "lessons_learned": writeup.lessons_learned if writeup else None,
        "lessons_learned_html": _md_to_html(writeup.lessons_learned if writeup else None),
        "reflection": writeup.reflection if writeup else None,
        "reflection_html": _md_to_html(writeup.reflection if writeup else None),
        "next_steps": writeup.next_steps if writeup else None,
        "next_steps_html": _md_to_html(writeup.next_steps if writeup else None),
        "structured_findings": [
            {"title": f.title, "description": f.description, "severity": f.severity} for f in structured_findings
        ],
        "skills": [s.name for s in lab.skills],
        "tools": [t.name for t in lab.tools],
        "techniques": [
            {
                "technique_id": lt.technique.technique_id,
                "name": lt.technique.name,
                "tactic": lt.technique.tactic,
                "justification": lt.justification,
            }
            for lt in lab.techniques
        ],
        "image_evidence": image_evidence,
        "file_evidence": file_evidence,
        "generated_at": _generated_at(),
    }


# ---- Learning summary --------------------------------------------------------


def build_learning_summary_context(db: Session, user_id, today: date) -> dict:
    return {
        "overview": stats_service.get_overview(db, user_id, today),
        "labs_by_category": stats_service.labs_by_category(db, user_id),
        "skills_practiced": stats_service.skills_practiced(db, user_id),
        "tools_used": stats_service.tools_used(db, user_id),
        "mitre_coverage": stats_service.mitre_coverage_by_tactic(db, user_id),
        "activity_timeline": stats_service.activity_timeline(db, user_id, today),
        "generated_at": _generated_at(),
    }


# ---- rendering ----------------------------------------------------------------


def render_report(template_base_name: str, context: dict, fmt: str) -> bytes:
    if fmt == "markdown":
        template = _jinja_env.get_template(f"{template_base_name}.md.jinja2")
        return template.render(**context).encode("utf-8")

    if fmt == "pdf":
        template = _jinja_env.get_template(f"{template_base_name}.html.jinja2")
        html = template.render(**context)
        return weasyprint.HTML(string=html).write_pdf()

    raise ValueError(f"Unsupported report format: {fmt}")
