"""
Tests for Milestone 6: CTF tracker.

Covers: event and challenge CRUD, category/difficulty/status validation,
skill/tool attach-detach (reusing the same master lists as labs),
technique mapping with the same required-justification and
unknown-technique guardrails as labs, evidence upload/list/download
reusing the same security pipeline, cascading deletes (event -> 
challenges -> evidence files), and ownership isolation between users.
"""

import io

import pytest

from app.seed.seed_data import seed_skills_and_tools

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

OTHER_USER = {
    "email": "other@example.com",
    "display_name": "Other Analyst",
    "password": "anotherpass9",
}

SAMPLE_EVENT = {"name": "PicoCTF 2026", "platform": "PicoCTF", "event_date": "2026-03-01"}

SAMPLE_CHALLENGE = {
    "title": "Baby's First Overflow",
    "category": "Pwn",
    "difficulty": "Easy",
    "status": "Unsolved",
}

VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture()
def seeded(db_session):
    seed_skills_and_tools(db_session)
    return db_session


def _register(client, user=VALID_USER):
    client.post("/api/v1/auth/register", json=user)


def _create_event_and_challenge(client) -> tuple[str, str]:
    _register(client)
    event = client.post("/api/v1/ctf-events", json=SAMPLE_EVENT).json()
    challenge = client.post(f"/api/v1/ctf-events/{event['id']}/challenges", json=SAMPLE_CHALLENGE).json()
    return event["id"], challenge["id"]


def test_create_ctf_event(client):
    _register(client)
    response = client.post("/api/v1/ctf-events", json=SAMPLE_EVENT)
    assert response.status_code == 201
    assert response.json()["name"] == SAMPLE_EVENT["name"]


def test_list_ctf_events_only_returns_own(client):
    _register(client)
    client.post("/api/v1/ctf-events", json=SAMPLE_EVENT)
    client.post("/api/v1/ctf-events", json={**SAMPLE_EVENT, "name": "HTB Cyber Apocalypse"})

    response = client.get("/api/v1/ctf-events")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_challenge_under_event(client):
    event_id, challenge_id = _create_event_and_challenge(client)
    response = client.get(f"/api/v1/ctf-challenges/{challenge_id}")
    assert response.status_code == 200
    assert response.json()["title"] == SAMPLE_CHALLENGE["title"]
    assert response.json()["ctf_event_id"] == event_id


def test_create_challenge_rejects_invalid_category(client):
    _register(client)
    event = client.post("/api/v1/ctf-events", json=SAMPLE_EVENT).json()
    response = client.post(
        f"/api/v1/ctf-events/{event['id']}/challenges",
        json={**SAMPLE_CHALLENGE, "category": "Not A Real Category"},
    )
    assert response.status_code == 422


def test_create_challenge_rejects_invalid_status(client):
    _register(client)
    event = client.post("/api/v1/ctf-events", json=SAMPLE_EVENT).json()
    response = client.post(
        f"/api/v1/ctf-events/{event['id']}/challenges",
        json={**SAMPLE_CHALLENGE, "status": "Half Solved"},
    )
    assert response.status_code == 422


def test_update_challenge_to_solved_with_writeup(client):
    _, challenge_id = _create_event_and_challenge(client)
    response = client.put(
        f"/api/v1/ctf-challenges/{challenge_id}",
        json={
            **SAMPLE_CHALLENGE,
            "status": "Solved",
            "solution_writeup": "Overwrote the return address to jump to the win() function.",
            "lessons_learned": "Stack canaries would have prevented this.",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Solved"
    assert "win()" in response.json()["solution_writeup"]


def test_event_detail_includes_challenges(client):
    event_id, challenge_id = _create_event_and_challenge(client)
    response = client.get(f"/api/v1/ctf-events/{event_id}")
    assert response.status_code == 200
    assert len(response.json()["challenges"]) == 1
    assert response.json()["challenges"][0]["id"] == challenge_id


def test_attach_skill_and_tool_to_challenge(client, seeded):
    _, challenge_id = _create_event_and_challenge(client)

    skill_response = client.post(f"/api/v1/ctf-challenges/{challenge_id}/skills", json={"name": "Reverse Engineering"})
    assert skill_response.status_code == 200
    assert skill_response.json()[0]["name"] == "Reverse Engineering"

    tool_response = client.post(f"/api/v1/ctf-challenges/{challenge_id}/tools", json={"name": "GDB"})
    assert tool_response.status_code == 200
    assert tool_response.json()[0]["name"] == "GDB"


def test_detach_skill_from_challenge(client, seeded):
    _, challenge_id = _create_event_and_challenge(client)
    skills = client.post(f"/api/v1/ctf-challenges/{challenge_id}/skills", json={"name": "Cryptography"}).json()

    response = client.delete(f"/api/v1/ctf-challenges/{challenge_id}/skills/{skills[0]['id']}")
    assert response.status_code == 200
    assert response.json() == []


def test_attach_technique_with_justification(client, seeded):
    _, challenge_id = _create_event_and_challenge(client)
    technique = next(t for t in client.get("/api/v1/mitre-techniques").json() if t["technique_id"] == "T1055")

    response = client.post(
        f"/api/v1/ctf-challenges/{challenge_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Injected shellcode into the running process."},
    )
    assert response.status_code == 200
    assert response.json()[0]["technique"]["technique_id"] == "T1055"


def test_attach_technique_rejects_short_justification(client, seeded):
    _, challenge_id = _create_event_and_challenge(client)
    technique = next(t for t in client.get("/api/v1/mitre-techniques").json() if t["technique_id"] == "T1055")

    response = client.post(
        f"/api/v1/ctf-challenges/{challenge_id}/techniques",
        json={"technique_id": technique["id"], "justification": "no"},
    )
    assert response.status_code == 422


def test_attach_technique_rejects_unknown_id(client):
    import uuid as uuid_module

    _, challenge_id = _create_event_and_challenge(client)
    response = client.post(
        f"/api/v1/ctf-challenges/{challenge_id}/techniques",
        json={"technique_id": str(uuid_module.uuid4()), "justification": "This technique does not exist at all."},
    )
    assert response.status_code == 400


def test_upload_and_download_ctf_evidence(client, isolated_evidence_storage):
    _, challenge_id = _create_event_and_challenge(client)

    upload_response = client.post(
        f"/api/v1/ctf-challenges/{challenge_id}/evidence",
        data={"evidence_type": "screenshot", "description": "Exploit output"},
        files={"file": ("exploit.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert upload_response.status_code == 201
    evidence_id = upload_response.json()["id"]

    download_response = client.get(f"/api/v1/ctf-evidence/{evidence_id}/file")
    assert download_response.status_code == 200
    assert download_response.content == VALID_PNG_BYTES
    assert "attachment" in download_response.headers["content-disposition"]


def test_ctf_evidence_upload_rejects_disallowed_extension(client):
    _, challenge_id = _create_event_and_challenge(client)
    response = client.post(
        f"/api/v1/ctf-challenges/{challenge_id}/evidence",
        data={"evidence_type": "report"},
        files={"file": ("exploit.exe", io.BytesIO(b"MZ fake exe"), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_delete_challenge_cascades_evidence_file(client, isolated_evidence_storage):
    _, challenge_id = _create_event_and_challenge(client)
    client.post(
        f"/api/v1/ctf-challenges/{challenge_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("exploit.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert len(list(isolated_evidence_storage.iterdir())) == 1

    response = client.delete(f"/api/v1/ctf-challenges/{challenge_id}")
    assert response.status_code == 204
    assert len(list(isolated_evidence_storage.iterdir())) == 0


def test_delete_event_cascades_challenges_and_evidence(client, db_session, isolated_evidence_storage):
    from app.models.ctf import CtfChallenge

    event_id, challenge_id = _create_event_and_challenge(client)
    client.post(
        f"/api/v1/ctf-challenges/{challenge_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("exploit.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )

    response = client.delete(f"/api/v1/ctf-events/{event_id}")
    assert response.status_code == 204

    db_session.expire_all()
    assert db_session.query(CtfChallenge).filter(CtfChallenge.id == challenge_id).count() == 0
    assert len(list(isolated_evidence_storage.iterdir())) == 0


def test_user_cannot_access_another_users_ctf_event(client, db_session):
    from app.models.ctf import CtfEvent
    from app.models.user import User
    from app.security import hash_password

    _register(client)  # logs the test client in as VALID_USER

    other_user = User(
        email=OTHER_USER["email"],
        display_name=OTHER_USER["display_name"],
        password_hash=hash_password(OTHER_USER["password"]),
    )
    db_session.add(other_user)
    db_session.flush()

    other_event = CtfEvent(user_id=other_user.id, name="Private CTF", platform="HTB")
    db_session.add(other_event)
    db_session.commit()
    db_session.refresh(other_event)

    response = client.get(f"/api/v1/ctf-events/{other_event.id}")
    assert response.status_code == 404


def test_ctf_options_endpoint(client):
    _register(client)
    response = client.get("/api/v1/ctf-options")
    assert response.status_code == 200
    body = response.json()
    assert "Pwn" in body["categories"]
    assert "Solved" in body["statuses"]


def test_ctf_endpoints_require_authentication(client):
    assert client.get("/api/v1/ctf-events").status_code == 401
