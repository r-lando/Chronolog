"""
Tests for Milestone 5: MITRE ATT&CK integration.

Covers: mapping a lab to an existing seeded technique with a
justification, rejecting justifications that are too short, rejecting
mappings to a technique id that doesn't exist (the anti-fabrication
guardrail), updating the justification on re-mapping, detaching,
technique list/detail stats scoped per-user, and the related-techniques
cross-reference now surfaced on skill/tool detail views.
"""

import uuid

import pytest

from app.seed.seed_data import seed_skills_and_tools

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

LAB_A = {
    "title": "Brute Force Detection Lab",
    "platform": "TryHackMe",
    "category": "SOC / Blue Team",
    "difficulty": "Medium",
    "status": "Completed",
    "date_completed": "2026-02-01",
}


@pytest.fixture()
def seeded(db_session):
    """
    Seeds the *same* session the test client's get_db override uses
    (see tests/conftest.py) — seed_skills_and_tools() takes a Session
    explicitly rather than opening its own, specifically so it can share
    the test's isolated in-memory database instead of the real
    production DATABASE_URL.
    """
    seed_skills_and_tools(db_session)
    return db_session


def _register_and_create_lab(client) -> str:
    client.post("/api/v1/auth/register", json=VALID_USER)
    lab = client.post("/api/v1/labs", json=LAB_A).json()
    return lab["id"]


def _find_technique(client, technique_code: str) -> dict:
    techniques = client.get("/api/v1/mitre-techniques").json()
    return next(t for t in techniques if t["technique_id"] == technique_code)


def test_seeded_techniques_are_listed(client, seeded):
    _register_and_create_lab(client)

    response = client.get("/api/v1/mitre-techniques")
    assert response.status_code == 200
    codes = {t["technique_id"] for t in response.json()}
    assert "T1110" in codes
    assert "T1566" in codes


def test_attach_technique_with_valid_justification(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1110")

    response = client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={
            "technique_id": technique["id"],
            "justification": "Observed repeated failed logon attempts (Event ID 4625) in the log data.",
        },
    )
    assert response.status_code == 200
    mappings = response.json()
    assert len(mappings) == 1
    assert mappings[0]["technique"]["technique_id"] == "T1110"
    assert "4625" in mappings[0]["justification"]


def test_attach_technique_rejects_short_justification(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1110")

    response = client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "yes"},
    )
    assert response.status_code == 422


def test_attach_technique_rejects_unknown_technique_id(client):
    lab_id = _register_and_create_lab(client)

    response = client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={
            "technique_id": str(uuid.uuid4()),
            "justification": "This technique id does not exist in the seeded reference list.",
        },
    )
    assert response.status_code == 400
    assert "Unknown MITRE technique" in response.json()["detail"]


def test_reattaching_technique_updates_justification(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1110")

    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "First justification text here."},
    )
    response = client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Updated, more detailed justification text."},
    )
    mappings = response.json()
    assert len(mappings) == 1  # still one mapping, not two
    assert mappings[0]["justification"] == "Updated, more detailed justification text."


def test_detach_technique(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1078")

    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Compromised valid credentials were used."},
    )
    response = client.delete(f"/api/v1/labs/{lab_id}/techniques/{technique['id']}")
    assert response.status_code == 200
    assert response.json() == []


def test_technique_stats_reflect_real_lab_data(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1110")

    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Brute force login attempts were observed."},
    )

    updated = _find_technique(client, "T1110")
    assert updated["lab_count"] == 1
    assert updated["last_practiced"] == "2026-02-01"


def test_technique_detail_includes_related_labs_with_justification(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1110")

    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Brute force login attempts were observed."},
    )

    detail = client.get(f"/api/v1/mitre-techniques/{technique['id']}").json()
    assert detail["lab_count"] == 1
    assert len(detail["related_labs"]) == 1
    assert detail["related_labs"][0]["lab"]["title"] == LAB_A["title"]
    assert detail["related_labs"][0]["justification"] == "Brute force login attempts were observed."


def test_technique_not_found_returns_404(client):
    _register_and_create_lab(client)
    response = client.get(f"/api/v1/mitre-techniques/{uuid.uuid4()}")
    assert response.status_code == 404


def test_lab_response_includes_attached_techniques(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1566")

    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "A phishing email was analyzed in this lab."},
    )

    fetched = client.get(f"/api/v1/labs/{lab_id}").json()
    assert len(fetched["techniques"]) == 1
    assert fetched["techniques"][0]["technique"]["technique_id"] == "T1566"


def test_skill_detail_includes_related_techniques(client, seeded):
    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1110")

    skill = client.post(f"/api/v1/labs/{lab_id}/skills", json={"name": "Threat Detection"}).json()[0]
    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Brute force login attempts were observed."},
    )

    detail = client.get(f"/api/v1/skills/{skill['id']}").json()
    assert len(detail["related_techniques"]) == 1
    assert detail["related_techniques"][0]["technique_id"] == "T1110"


def test_deleting_lab_removes_technique_mappings(client, seeded):
    from app.models.mitre import LabTechnique

    lab_id = _register_and_create_lab(client)
    technique = _find_technique(client, "T1110")

    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Brute force login attempts were observed."},
    )

    delete_response = client.delete(f"/api/v1/labs/{lab_id}")
    assert delete_response.status_code == 204

    seeded.expire_all()
    assert seeded.query(LabTechnique).filter(LabTechnique.lab_id == lab_id).count() == 0


def test_mitre_endpoints_require_authentication(client):
    assert client.get("/api/v1/mitre-techniques").status_code == 401
