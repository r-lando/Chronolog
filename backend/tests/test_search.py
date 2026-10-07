"""
Tests for Milestone 11: global search.

Covers: finding matches across labs, CTF challenges, findings, tags,
skills, tools, and MITRE techniques; that owned-data searches (labs,
CTFs, findings, tags) are correctly scoped to the current user; that
shared reference data (skills, tools, techniques) matches regardless of
whether the current user has used it yet; and that an empty/no-match
query returns an empty list rather than erroring.
"""

import pytest

from app.seed.seed_data import seed_skills_and_tools

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

SAMPLE_LAB = {
    "title": "Phishing Email Investigation",
    "platform": "TryHackMe",
    "category": "SOC / Blue Team",
    "difficulty": "Medium",
    "status": "Completed",
}


@pytest.fixture()
def seeded(db_session):
    seed_skills_and_tools(db_session)
    return db_session


def _register(client):
    client.post("/api/v1/auth/register", json=VALID_USER)


def _result_titles(response_json, result_type=None):
    results = response_json["results"]
    if result_type:
        results = [r for r in results if r["type"] == result_type]
    return [r["title"] for r in results]


def test_search_finds_lab_by_title(client):
    _register(client)
    client.post("/api/v1/labs", json=SAMPLE_LAB)

    response = client.get("/api/v1/search", params={"q": "phishing"})
    assert response.status_code == 200
    assert "Phishing Email Investigation" in _result_titles(response.json(), "lab")


def test_search_finds_lab_by_description(client):
    _register(client)
    client.post("/api/v1/labs", json={**SAMPLE_LAB, "description": "Analyzed a suspicious attachment."})

    response = client.get("/api/v1/search", params={"q": "suspicious attachment"})
    assert "Phishing Email Investigation" in _result_titles(response.json(), "lab")


def test_search_finds_ctf_challenge(client):
    _register(client)
    event = client.post("/api/v1/ctf-events", json={"name": "PicoCTF"}).json()
    client.post(
        f"/api/v1/ctf-events/{event['id']}/challenges",
        json={"title": "RSA Basics", "category": "Crypto", "difficulty": "Easy", "status": "Solved"},
    )

    response = client.get("/api/v1/search", params={"q": "RSA"})
    results = [r for r in response.json()["results"] if r["type"] == "ctf_challenge"]
    assert len(results) == 1
    assert results[0]["subtitle"] == "PicoCTF"


def test_search_finds_finding_with_lab_context(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=SAMPLE_LAB).json()
    client.post(f"/api/v1/labs/{lab['id']}/findings", json={"title": "Malicious macro detected"})

    response = client.get("/api/v1/search", params={"q": "macro"})
    results = [r for r in response.json()["results"] if r["type"] == "finding"]
    assert len(results) == 1
    assert SAMPLE_LAB["title"] in results[0]["subtitle"]


def test_search_finds_tag_used_on_own_lab(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=SAMPLE_LAB).json()
    client.post(f"/api/v1/labs/{lab['id']}/tags", json={"name": "social-engineering"})

    response = client.get("/api/v1/search", params={"q": "social"})
    assert "social-engineering" in _result_titles(response.json(), "tag")


def test_search_finds_shared_skill_regardless_of_usage(client, seeded):
    """Skills are shared reference data — a match appears even if the user has never attached it to a lab."""
    _register(client)
    response = client.get("/api/v1/search", params={"q": "Threat Hunting"})
    assert "Threat Hunting" in _result_titles(response.json(), "skill")


def test_search_finds_shared_tool(client, seeded):
    _register(client)
    response = client.get("/api/v1/search", params={"q": "Wireshark"})
    assert "Wireshark" in _result_titles(response.json(), "tool")


def test_search_finds_mitre_technique_by_name_or_code(client, seeded):
    _register(client)

    by_name = client.get("/api/v1/search", params={"q": "Brute Force"}).json()
    by_code = client.get("/api/v1/search", params={"q": "T1110"}).json()

    assert any(r["type"] == "mitre_technique" for r in by_name["results"])
    assert any(r["type"] == "mitre_technique" for r in by_code["results"])


def test_search_with_no_matches_returns_empty_list(client, seeded):
    _register(client)
    response = client.get("/api/v1/search", params={"q": "xyznonexistentquery"})
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_does_not_return_another_users_labs(client, db_session):
    from app.models.lab import Lab
    from app.models.user import User
    from app.security import hash_password

    _register(client)
    other_user = User(email="other@example.com", display_name="Other", password_hash=hash_password("anotherpass9"))
    db_session.add(other_user)
    db_session.flush()
    db_session.add(Lab(user_id=other_user.id, **SAMPLE_LAB))
    db_session.commit()

    response = client.get("/api/v1/search", params={"q": "phishing"})
    assert _result_titles(response.json(), "lab") == []


def test_search_requires_authentication(client):
    assert client.get("/api/v1/search", params={"q": "test"}).status_code == 401


def test_search_rejects_empty_query(client):
    _register(client)
    response = client.get("/api/v1/search", params={"q": ""})
    assert response.status_code == 422
