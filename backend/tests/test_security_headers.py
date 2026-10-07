"""
Tests for Milestone 11: security headers middleware.

Covers: the defense-in-depth headers are present on every response
(not just specific routes, including a 404), and HSTS is only sent when
cookie_secure is enabled — it would be actively wrong advice to tell a
browser "always use HTTPS" while serving plain HTTP in local dev.

The docs_url=None-in-production behavior in app/main.py isn't covered
by an automated test here: the FastAPI app instance (and its docs_url)
is constructed once at import time from whatever ENVIRONMENT was set
when the test process started, so exercising both branches would mean
re-importing the app module under a different environment mid-test-run
— more complexity than the behavior warrants. It's straightforward
enough to verify by reading app/main.py directly.
"""

from app.config import get_settings


def test_security_headers_present_on_every_response(client):
    response = client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_security_headers_present_even_on_404(client):
    """Headers should be added by middleware regardless of the route outcome, including errors."""
    response = client.get("/api/v1/this-route-does-not-exist")
    assert response.status_code == 404
    assert response.headers["x-content-type-options"] == "nosniff"


def test_hsts_not_sent_when_cookie_secure_is_disabled(client):
    settings = get_settings()
    assert settings.cookie_secure is False  # the test/dev default
    response = client.get("/api/v1/health")
    assert "strict-transport-security" not in response.headers


def test_hsts_sent_when_cookie_secure_is_enabled(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "cookie_secure", True)
    response = client.get("/api/v1/health")
    assert "strict-transport-security" in response.headers
