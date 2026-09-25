"""
Tests for Milestone 1: authentication.

Covers: successful register/login, wrong-password rejection, generic
error messages (no user enumeration), cookie-based session access to
/auth/me, logout clearing the session, and single-user registration
lockout.
"""


VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}


def test_register_creates_user_and_sets_cookie(client):
    response = client.post("/api/v1/auth/register", json=VALID_USER)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == VALID_USER["email"]
    assert "password" not in body
    assert "password_hash" not in body
    assert "tala_access_token" in response.cookies


def test_register_rejects_weak_password(client):
    weak = {**VALID_USER, "password": "alllettersnodigits"}
    response = client.post("/api/v1/auth/register", json=weak)
    assert response.status_code == 422


def test_second_registration_blocked_in_single_user_mode(client):
    first = client.post("/api/v1/auth/register", json=VALID_USER)
    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register",
        json={**VALID_USER, "email": "someoneelse@example.com"},
    )
    assert second.status_code == 403


def test_login_success(client):
    client.post("/api/v1/auth/register", json=VALID_USER)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert response.status_code == 200
    assert "tala_access_token" in response.cookies


def test_login_wrong_password_returns_generic_error(client):
    client.post("/api/v1/auth/register", json=VALID_USER)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": VALID_USER["email"], "password": "wrongpassword1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_returns_same_generic_error(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_when_authenticated(client):
    client.post("/api/v1/auth/register", json=VALID_USER)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == VALID_USER["email"]


def test_logout_clears_session(client):
    client.post("/api/v1/auth/register", json=VALID_USER)
    assert client.get("/api/v1/auth/me").status_code == 200

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    assert client.get("/api/v1/auth/me").status_code == 401
