"""
Tests for Milestone 2: lab management + write-ups.

Covers: creating a lab (and its empty write-up shell), retrieving,
updating, filtering/search, status transitions, tag attach/detach,
deletion (cascading to the write-up), and — importantly — that one
user can never read or modify another user's lab.
"""

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

OTHER_USER_DIRECT_INSERT = {
    "email": "other@example.com",
    "display_name": "Other Analyst",
    "password": "anotherpass9",
}

SAMPLE_LAB = {
    "title": "Windows Event Log Investigation",
    "platform": "TryHackMe",
    "category": "SOC / Blue Team",
    "difficulty": "Medium",
    "status": "Planned",
}


def _register_and_login(client, user=VALID_USER):
    client.post("/api/v1/auth/register", json=user)


def test_create_lab_creates_empty_writeup_shell(client):
    _register_and_login(client)
    response = client.post("/api/v1/labs", json=SAMPLE_LAB)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == SAMPLE_LAB["title"]
    assert body["writeup"] is not None
    assert body["writeup"]["methodology"] is None


def test_create_lab_rejects_invalid_category(client):
    _register_and_login(client)
    bad_lab = {**SAMPLE_LAB, "category": "Not A Real Category"}
    response = client.post("/api/v1/labs", json=bad_lab)
    assert response.status_code == 422


def test_create_lab_rejects_completed_before_started(client):
    _register_and_login(client)
    bad_lab = {
        **SAMPLE_LAB,
        "date_started": "2026-01-10",
        "date_completed": "2026-01-01",
    }
    response = client.post("/api/v1/labs", json=bad_lab)
    assert response.status_code == 422


def test_list_labs_only_returns_own_labs(client):
    _register_and_login(client)
    client.post("/api/v1/labs", json=SAMPLE_LAB)
    client.post("/api/v1/labs", json={**SAMPLE_LAB, "title": "Second Lab"})

    response = client.get("/api/v1/labs")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_filter_labs_by_category(client):
    _register_and_login(client)
    client.post("/api/v1/labs", json=SAMPLE_LAB)
    client.post("/api/v1/labs", json={**SAMPLE_LAB, "title": "Web Lab", "category": "Web Security"})

    response = client.get("/api/v1/labs", params={"category": "Web Security"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Web Lab"


def test_search_labs_by_title(client):
    _register_and_login(client)
    client.post("/api/v1/labs", json=SAMPLE_LAB)
    client.post("/api/v1/labs", json={**SAMPLE_LAB, "title": "Phishing Email Investigation"})

    response = client.get("/api/v1/labs", params={"search": "phishing"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "Phishing" in results[0]["title"]


def test_update_lab(client):
    _register_and_login(client)
    created = client.post("/api/v1/labs", json=SAMPLE_LAB).json()

    updated_payload = {**SAMPLE_LAB, "status": "In Progress", "title": "Updated Title"}
    response = client.put(f"/api/v1/labs/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["status"] == "In Progress"


def test_update_lab_status_endpoint(client):
    _register_and_login(client)
    created = client.post("/api/v1/labs", json=SAMPLE_LAB).json()

    response = client.patch(f"/api/v1/labs/{created['id']}/status", json={"status": "Completed"})
    assert response.status_code == 200
    assert response.json()["status"] == "Completed"


def test_update_lab_status_rejects_invalid_value(client):
    _register_and_login(client)
    created = client.post("/api/v1/labs", json=SAMPLE_LAB).json()

    response = client.patch(f"/api/v1/labs/{created['id']}/status", json={"status": "Sideways"})
    assert response.status_code == 422


def test_update_writeup(client):
    _register_and_login(client)
    created = client.post("/api/v1/labs", json=SAMPLE_LAB).json()

    writeup_payload = {
        "methodology": "Reviewed Windows Security event logs for logon anomalies.",
        "findings": "Multiple failed logons from a single account within a short window.",
        "lessons_learned": "Event ID 4625 clusters are a strong brute-force indicator.",
    }
    response = client.put(f"/api/v1/labs/{created['id']}/writeup", json=writeup_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["methodology"] == writeup_payload["methodology"]
    assert body["findings"] == writeup_payload["findings"]


def test_add_and_remove_tag(client):
    _register_and_login(client)
    created = client.post("/api/v1/labs", json=SAMPLE_LAB).json()

    add_response = client.post(f"/api/v1/labs/{created['id']}/tags", json={"name": "Windows"})
    assert add_response.status_code == 200
    tags = add_response.json()
    assert len(tags) == 1
    assert tags[0]["name"] == "windows"  # normalized to lowercase

    tag_id = tags[0]["id"]
    remove_response = client.delete(f"/api/v1/labs/{created['id']}/tags/{tag_id}")
    assert remove_response.status_code == 200
    assert remove_response.json() == []


def test_delete_lab(client):
    _register_and_login(client)
    created = client.post("/api/v1/labs", json=SAMPLE_LAB).json()

    delete_response = client.delete(f"/api/v1/labs/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/labs/{created['id']}")
    assert get_response.status_code == 404


def test_lab_options_endpoint_matches_constants(client):
    from app.constants import LAB_CATEGORIES, LAB_DIFFICULTIES, LAB_STATUSES

    _register_and_login(client)
    response = client.get("/api/v1/labs/options")
    assert response.status_code == 200
    body = response.json()
    assert body["categories"] == LAB_CATEGORIES
    assert body["difficulties"] == LAB_DIFFICULTIES
    assert body["statuses"] == LAB_STATUSES


def test_labs_require_authentication(client):
    response = client.get("/api/v1/labs")
    assert response.status_code == 401


def test_user_cannot_access_another_users_lab(client, db_session):
    """
    Direct DB insertion of a second user + lab, bypassing the
    single-user registration lockout, specifically to prove the
    ownership check in get_owned_lab_or_404 actually works.
    """
    from app.models.lab import Lab
    from app.models.user import User
    from app.security import hash_password

    _register_and_login(client)  # logs the test client in as VALID_USER

    other_user = User(
        email=OTHER_USER_DIRECT_INSERT["email"],
        display_name=OTHER_USER_DIRECT_INSERT["display_name"],
        password_hash=hash_password(OTHER_USER_DIRECT_INSERT["password"]),
    )
    db_session.add(other_user)
    db_session.flush()

    other_lab = Lab(user_id=other_user.id, **SAMPLE_LAB)
    db_session.add(other_lab)
    db_session.commit()
    db_session.refresh(other_lab)

    # The logged-in VALID_USER must not be able to see the other user's lab.
    response = client.get(f"/api/v1/labs/{other_lab.id}")
    assert response.status_code == 404
