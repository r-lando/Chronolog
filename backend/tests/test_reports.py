"""
Tests for Milestone 10: reports + export.

Covers: format validation, Markdown content correctness for both report
types, the PDF path producing real PDF bytes (checked via the %PDF-
magic number, since asserting exact binary content isn't meaningful),
ownership enforcement on lab reports, and — importantly — that reports
are a private export and therefore DO include the Reflection field,
unlike the public portfolio view from Milestone 9 which deliberately
excludes it. These are different boundaries for different purposes and
both need their own test coverage.
"""

import io

import pytest

from app.seed.seed_data import seed_skills_and_tools

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

SAMPLE_LAB = {
    "title": "Windows Event Log Investigation",
    "platform": "TryHackMe",
    "category": "SOC / Blue Team",
    "difficulty": "Medium",
    "status": "Completed",
    "date_completed": "2026-01-12",
    "time_spent_minutes": 90,
}

VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture()
def seeded(db_session):
    seed_skills_and_tools(db_session)
    return db_session


def _register_and_create_lab(client) -> str:
    client.post("/api/v1/auth/register", json=VALID_USER)
    lab = client.post("/api/v1/labs", json=SAMPLE_LAB).json()
    return lab["id"]


def _write_full_writeup(client, lab_id: str):
    client.put(
        f"/api/v1/labs/{lab_id}/writeup",
        json={
            "methodology": "Reviewed Windows Security event logs for anomalies.",
            "findings": "Multiple failed logons from a single account.",
            "analysis": "This pattern is consistent with a brute-force attempt.",
            "lessons_learned": "Event ID 4625 clusters are a strong indicator.",
            "reflection": "I found the log filtering syntax confusing at first.",
            "next_steps": "Practice building more advanced SIEM queries.",
        },
    )


# ---- format validation -----------------------------------------------------------


def test_lab_report_rejects_invalid_format(client):
    lab_id = _register_and_create_lab(client)
    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "docx"})
    assert response.status_code == 400


def test_learning_summary_rejects_invalid_format(client):
    _register_and_create_lab(client)
    response = client.get("/api/v1/reports/learning-summary", params={"format": "docx"})
    assert response.status_code == 400


def test_lab_report_defaults_to_markdown(client):
    lab_id = _register_and_create_lab(client)
    response = client.get(f"/api/v1/labs/{lab_id}/report")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")


# ---- lab report content -----------------------------------------------------------


def test_lab_report_markdown_includes_core_fields(client):
    lab_id = _register_and_create_lab(client)
    _write_full_writeup(client, lab_id)

    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "markdown"})
    assert response.status_code == 200
    content = response.content.decode("utf-8")

    assert SAMPLE_LAB["title"] in content
    assert "brute-force" in content
    assert "4625" in content
    assert "advanced SIEM" in content


def test_lab_report_includes_reflection_unlike_public_portfolio(client):
    """
    This is the key distinction from Milestone 9: the portfolio view
    strips Reflection automatically because it's shown to strangers.
    A report is a private export the owner explicitly downloads for
    themselves, so it includes everything, Reflection included.
    """
    lab_id = _register_and_create_lab(client)
    _write_full_writeup(client, lab_id)

    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "markdown"})
    content = response.content.decode("utf-8")
    assert "confusing" in content


def test_lab_report_includes_structured_findings_and_techniques(client, seeded):
    lab_id = _register_and_create_lab(client)
    client.post(f"/api/v1/labs/{lab_id}/findings", json={"title": "Brute force detected", "severity": "High"})
    technique = next(t for t in client.get("/api/v1/mitre-techniques").json() if t["technique_id"] == "T1110")
    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Repeated failed logons observed."},
    )

    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "markdown"})
    content = response.content.decode("utf-8")
    assert "Brute force detected" in content
    assert "T1110" in content


def test_lab_report_lists_all_evidence_including_private(client):
    """A private report is for the owner — unlike the portfolio, it is not limited to is_public evidence."""
    lab_id = _register_and_create_lab(client)
    client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "log", "description": "Private auth log"},
        files={"file": ("auth.log", io.BytesIO(b"2026-01-12 failed login\n"), "text/plain")},
    )
    # evidence left at its default is_public=False

    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "markdown"})
    content = response.content.decode("utf-8")
    assert "auth.log" in content
    assert "Private auth log" in content


def test_lab_report_embeds_image_evidence_inline_in_pdf(client):
    lab_id = _register_and_create_lab(client)
    client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )

    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "pdf"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_lab_report_requires_ownership(client, db_session):
    from app.models.lab import Lab
    from app.models.user import User
    from app.security import hash_password

    _register_and_create_lab(client)
    other_user = User(email="other@example.com", display_name="Other", password_hash=hash_password("anotherpass9"))
    db_session.add(other_user)
    db_session.flush()
    other_lab = Lab(user_id=other_user.id, **SAMPLE_LAB)
    db_session.add(other_lab)
    db_session.commit()
    db_session.refresh(other_lab)

    response = client.get(f"/api/v1/labs/{other_lab.id}/report")
    assert response.status_code == 404


def test_lab_report_handles_lab_with_no_writeup_content(client):
    """A freshly created lab has an empty write-up shell — the report must not error on all-None fields."""
    lab_id = _register_and_create_lab(client)
    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "markdown"})
    assert response.status_code == 200
    response_pdf = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "pdf"})
    assert response_pdf.status_code == 200
    assert response_pdf.content.startswith(b"%PDF-")


def test_lab_report_requires_authentication(client):
    assert client.get("/api/v1/labs/00000000-0000-0000-0000-000000000000/report").status_code == 401


# ---- learning summary content --------------------------------------------------------


def test_learning_summary_markdown_reflects_real_data(client, seeded):
    client.post("/api/v1/auth/register", json=VALID_USER)
    lab = client.post("/api/v1/labs", json=SAMPLE_LAB).json()
    client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "Log Analysis"})
    client.post(f"/api/v1/labs/{lab['id']}/tools", json={"name": "Splunk"})

    response = client.get("/api/v1/reports/learning-summary", params={"format": "markdown"})
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Labs completed | 1" in content
    assert "Log Analysis" in content
    assert "Splunk" in content


def test_learning_summary_handles_empty_account(client):
    client.post("/api/v1/auth/register", json=VALID_USER)
    response = client.get("/api/v1/reports/learning-summary", params={"format": "markdown"})
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "No practiced labs yet" in content


def test_learning_summary_pdf_is_valid(client):
    client.post("/api/v1/auth/register", json=VALID_USER)
    response = client.get("/api/v1/reports/learning-summary", params={"format": "pdf"})
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")


def test_learning_summary_only_reflects_own_data(client, db_session):
    from datetime import date

    from app.models.lab import Lab
    from app.models.user import User
    from app.security import hash_password

    client.post("/api/v1/auth/register", json=VALID_USER)

    other_user = User(email="other@example.com", display_name="Other", password_hash=hash_password("anotherpass9"))
    db_session.add(other_user)
    db_session.flush()
    db_session.add(
        Lab(
            user_id=other_user.id,
            title="Someone Else's Lab",
            category="Linux",
            difficulty="Easy",
            status="Completed",
            date_completed=date(2026, 1, 1),
        )
    )
    db_session.commit()

    response = client.get("/api/v1/reports/learning-summary", params={"format": "markdown"})
    content = response.content.decode("utf-8")
    assert "Labs completed | 0" in content
    assert "Someone Else" not in content


def test_learning_summary_requires_authentication(client):
    assert client.get("/api/v1/reports/learning-summary").status_code == 401


# ---- Content-Disposition filenames ------------------------------------------------


def test_lab_report_has_attachment_filename(client):
    lab_id = _register_and_create_lab(client)
    response = client.get(f"/api/v1/labs/{lab_id}/report", params={"format": "pdf"})
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert ".pdf" in disposition


def test_lab_report_filename_sanitizes_special_characters(client):
    import re

    client.post("/api/v1/auth/register", json=VALID_USER)
    lab = client.post(
        "/api/v1/labs", json={**SAMPLE_LAB, "title": 'Weird "Title" / With <Special> Chars!'}
    ).json()

    response = client.get(f"/api/v1/labs/{lab['id']}/report", params={"format": "markdown"})
    disposition = response.headers["content-disposition"]

    match = re.search(r'filename="([^"]*)"', disposition)
    assert match is not None, f"Could not find a quoted filename in: {disposition}"
    filename = match.group(1)

    # The sanitized filename must contain only safe characters — none of
    # the title's quotes, slashes, or angle brackets should survive.
    assert re.fullmatch(r"[a-z0-9\-]+\.md", filename), f"Unsafe filename produced: {filename}"
