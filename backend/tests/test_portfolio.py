"""
Tests for Milestone 9: portfolio mode + public write-ups.

The central property under test: the public endpoints never expose
private data, under any combination of states. Specifically:
- A lab must be explicitly marked portfolio-ready to appear publicly.
- The write-up's `reflection` field never appears publicly, published
  or not.
- Evidence only appears publicly if individually marked is_public=True
  — publishing a lab does not retroactively expose its files.
- An evidence item's `notes` field never appears publicly, even when
  the evidence itself is public.
- Unpublishing a lab immediately cuts off both its public page and its
  previously-public evidence files.
- The public endpoints require no authentication at all, and a user can
  only toggle portfolio status on their own labs.
"""

import io

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
}

VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


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
            "reflection": "I personally found the log filtering syntax confusing at first and made several mistakes before getting the query right.",
            "next_steps": "Practice building more advanced SIEM queries.",
        },
    )


def _publish(client, lab_id: str):
    response = client.patch(f"/api/v1/labs/{lab_id}/portfolio", json={"is_portfolio_ready": True})
    assert response.status_code == 200
    return response.json()


def _unpublish(client, lab_id: str):
    response = client.patch(f"/api/v1/labs/{lab_id}/portfolio", json={"is_portfolio_ready": False})
    assert response.status_code == 200
    return response.json()


# ---- publish / unpublish lifecycle -----------------------------------------------


def test_publishing_a_lab_generates_a_slug(client):
    lab_id = _register_and_create_lab(client)
    lab = _publish(client, lab_id)
    assert lab["is_portfolio_ready"] is True
    assert lab["portfolio_slug"] is not None
    assert len(lab["portfolio_slug"]) > 8


def test_unpublished_lab_does_not_appear_in_public_listing(client):
    _register_and_create_lab(client)
    response = client.get("/api/v1/public/portfolio")
    assert response.status_code == 200
    assert response.json() == []


def test_published_lab_appears_in_public_listing(client):
    lab_id = _register_and_create_lab(client)
    lab = _publish(client, lab_id)

    response = client.get("/api/v1/public/portfolio")
    assert response.status_code == 200
    slugs = [entry["slug"] for entry in response.json()]
    assert lab["portfolio_slug"] in slugs


def test_unpublishing_removes_lab_from_public_listing_and_detail(client):
    lab_id = _register_and_create_lab(client)
    lab = _publish(client, lab_id)
    slug = lab["portfolio_slug"]

    assert client.get(f"/api/v1/public/portfolio/{slug}").status_code == 200

    _unpublish(client, lab_id)

    assert client.get("/api/v1/public/portfolio").json() == []
    assert client.get(f"/api/v1/public/portfolio/{slug}").status_code == 404


def test_slug_is_stable_across_unpublish_and_republish(client):
    lab_id = _register_and_create_lab(client)
    first = _publish(client, lab_id)
    _unpublish(client, lab_id)
    second = _publish(client, lab_id)
    assert first["portfolio_slug"] == second["portfolio_slug"]


def test_portfolio_toggle_requires_authentication(client):
    lab_id = _register_and_create_lab(client)
    client.post("/api/v1/auth/logout")
    response = client.patch(f"/api/v1/labs/{lab_id}/portfolio", json={"is_portfolio_ready": True})
    assert response.status_code == 401


def test_user_cannot_publish_another_users_lab(client, db_session):
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

    response = client.patch(f"/api/v1/labs/{other_lab.id}/portfolio", json={"is_portfolio_ready": True})
    assert response.status_code == 404


def test_nonexistent_slug_returns_404(client):
    response = client.get("/api/v1/public/portfolio/this-slug-does-not-exist")
    assert response.status_code == 404


# ---- content sanitization: the core safety property -----------------------------


def test_public_view_never_includes_reflection(client):
    lab_id = _register_and_create_lab(client)
    _write_full_writeup(client, lab_id)
    lab = _publish(client, lab_id)

    public_view = client.get(f"/api/v1/public/portfolio/{lab['portfolio_slug']}").json()
    assert "reflection" not in public_view
    # Belt and suspenders: the sensitive sentence must not appear anywhere in the response.
    assert "confusing" not in str(public_view)
    assert "mistakes" not in str(public_view)


def test_public_view_includes_the_intended_writeup_sections(client):
    lab_id = _register_and_create_lab(client)
    _write_full_writeup(client, lab_id)
    lab = _publish(client, lab_id)

    public_view = client.get(f"/api/v1/public/portfolio/{lab['portfolio_slug']}").json()
    assert "brute-force" in public_view["analysis"]
    assert "4625" in public_view["lessons_learned"]
    assert "advanced SIEM" in public_view["next_steps"]


def test_private_evidence_is_never_shown_publicly(client):
    lab_id = _register_and_create_lab(client)
    client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot", "description": "private screenshot"},
        files={"file": ("private.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    lab = _publish(client, lab_id)

    public_view = client.get(f"/api/v1/public/portfolio/{lab['portfolio_slug']}").json()
    assert public_view["evidence"] == []


def test_evidence_marked_public_appears_but_without_notes(client):
    lab_id = _register_and_create_lab(client)
    uploaded = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot", "description": "Shown publicly"},
        files={"file": ("public.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    ).json()
    client.patch(
        f"/api/v1/evidence/{uploaded['id']}",
        json={"is_public": True, "notes": "Internal note: this box had an unpatched CVE, don't mention externally."},
    )

    lab = _publish(client, lab_id)
    public_view = client.get(f"/api/v1/public/portfolio/{lab['portfolio_slug']}").json()

    assert len(public_view["evidence"]) == 1
    assert public_view["evidence"][0]["description"] == "Shown publicly"
    assert "notes" not in public_view["evidence"][0]
    assert "CVE" not in str(public_view)


def test_publishing_a_lab_does_not_retroactively_expose_existing_evidence(client):
    """Evidence uploaded before publishing stays private by default — publishing is not opt-out."""
    lab_id = _register_and_create_lab(client)
    client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("screenshot.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    lab = _publish(client, lab_id)

    public_view = client.get(f"/api/v1/public/portfolio/{lab['portfolio_slug']}").json()
    assert public_view["evidence"] == []


def test_public_view_includes_skills_tools_and_techniques(client, db_session):
    from app.seed.seed_data import seed_skills_and_tools

    seed_skills_and_tools(db_session)

    lab_id = _register_and_create_lab(client)
    client.post(f"/api/v1/labs/{lab_id}/skills", json={"name": "Log Analysis"})
    client.post(f"/api/v1/labs/{lab_id}/tools", json={"name": "Splunk"})
    technique = next(t for t in client.get("/api/v1/mitre-techniques").json() if t["technique_id"] == "T1110")
    client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Observed repeated failed logon attempts."},
    )

    lab = _publish(client, lab_id)
    public_view = client.get(f"/api/v1/public/portfolio/{lab['portfolio_slug']}").json()

    assert "Log Analysis" in public_view["skills"]
    assert "Splunk" in public_view["tools"]
    assert public_view["techniques"][0]["technique_id"] == "T1110"


# ---- public evidence file access --------------------------------------------------


def test_public_evidence_file_downloadable_when_lab_published_and_evidence_public(client):
    lab_id = _register_and_create_lab(client)
    uploaded = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    ).json()
    client.patch(f"/api/v1/evidence/{uploaded['id']}", json={"is_public": True})
    _publish(client, lab_id)

    response = client.get(f"/api/v1/public/evidence/{uploaded['id']}/file")
    assert response.status_code == 200
    assert response.content == VALID_PNG_BYTES
    assert "attachment" in response.headers["content-disposition"]


def test_public_evidence_file_requires_no_authentication(client):
    lab_id = _register_and_create_lab(client)
    uploaded = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    ).json()
    client.patch(f"/api/v1/evidence/{uploaded['id']}", json={"is_public": True})
    _publish(client, lab_id)

    client.post("/api/v1/auth/logout")
    response = client.get(f"/api/v1/public/evidence/{uploaded['id']}/file")
    assert response.status_code == 200


def test_public_evidence_file_blocked_if_evidence_not_marked_public(client):
    lab_id = _register_and_create_lab(client)
    uploaded = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    ).json()
    _publish(client, lab_id)  # lab published, but evidence never marked public

    response = client.get(f"/api/v1/public/evidence/{uploaded['id']}/file")
    assert response.status_code == 404


def test_public_evidence_file_blocked_if_lab_not_published(client):
    lab_id = _register_and_create_lab(client)
    uploaded = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    ).json()
    client.patch(f"/api/v1/evidence/{uploaded['id']}", json={"is_public": True})
    # lab never published

    response = client.get(f"/api/v1/public/evidence/{uploaded['id']}/file")
    assert response.status_code == 404


def test_unpublishing_lab_immediately_blocks_previously_public_evidence(client):
    lab_id = _register_and_create_lab(client)
    uploaded = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot"},
        files={"file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    ).json()
    client.patch(f"/api/v1/evidence/{uploaded['id']}", json={"is_public": True})
    _publish(client, lab_id)

    assert client.get(f"/api/v1/public/evidence/{uploaded['id']}/file").status_code == 200

    _unpublish(client, lab_id)
    assert client.get(f"/api/v1/public/evidence/{uploaded['id']}/file").status_code == 404
