"""
End-to-end workflow test (spec section 21):

    Create Lab
    -> Add Write-up
    -> Add Evidence
    -> Add Skills
    -> Add Tools
    -> Add MITRE Technique
    -> Complete Lab
    -> Mark Portfolio Ready
    -> View Public Write-up

Every other test file in this suite verifies one feature in isolation.
This one walks the entire real user journey in a single test, in order,
re-fetching from the API after each step to confirm the previous step's
effects actually persisted and are visible to the next — which is a
different (and in some ways stronger) check than each feature's unit
tests provide on their own.
"""

import io

from app.seed.seed_data import seed_skills_and_tools

USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def test_full_lab_documentation_workflow(client, db_session):
    seed_skills_and_tools(db_session)

    # --- Register -----------------------------------------------------------
    register_response = client.post("/api/v1/auth/register", json=USER)
    assert register_response.status_code == 201

    # --- Create Lab -----------------------------------------------------------
    create_response = client.post(
        "/api/v1/labs",
        json={
            "title": "Brute Force Detection Lab",
            "platform": "TryHackMe",
            "category": "SOC / Blue Team",
            "difficulty": "Medium",
            "status": "In Progress",
            "date_started": "2026-03-01",
            "objective": "Detect brute-force login attempts from Windows Security event logs.",
        },
    )
    assert create_response.status_code == 201
    lab = create_response.json()
    lab_id = lab["id"]
    assert lab["writeup"] is not None  # empty shell created automatically

    # --- Add Write-up -----------------------------------------------------------
    writeup_response = client.put(
        f"/api/v1/labs/{lab_id}/writeup",
        json={
            "methodology": "Filtered Security event logs for Event ID 4625 (failed logon).",
            "findings": "20 failed logon attempts for the 'admin' account within 2 minutes from one host.",
            "analysis": "The volume and timing are consistent with an automated brute-force attempt.",
            "lessons_learned": "Clustering failed logons by account and source host is a fast detection signal.",
            "reflection": "Took a while to get the log query filters right.",
            "next_steps": "Build a detection rule to alert automatically on this pattern.",
        },
    )
    assert writeup_response.status_code == 200
    assert "4625" in writeup_response.json()["findings"]

    fetched_after_writeup = client.get(f"/api/v1/labs/{lab_id}").json()
    assert "brute-force" in fetched_after_writeup["writeup"]["analysis"]

    # --- Add Evidence -----------------------------------------------------------
    evidence_response = client.post(
        f"/api/v1/labs/{lab_id}/evidence",
        data={"evidence_type": "screenshot", "description": "Event Viewer showing failed logon cluster"},
        files={"file": ("event_viewer.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert evidence_response.status_code == 201
    evidence_id = evidence_response.json()["id"]

    evidence_list = client.get(f"/api/v1/labs/{lab_id}/evidence").json()
    assert len(evidence_list) == 1
    assert evidence_list[0]["id"] == evidence_id

    # --- Add Skills -----------------------------------------------------------
    skills_response = client.post(f"/api/v1/labs/{lab_id}/skills", json={"name": "Log Analysis"})
    assert skills_response.status_code == 200
    client.post(f"/api/v1/labs/{lab_id}/skills", json={"name": "Threat Detection"})

    # --- Add Tools -----------------------------------------------------------
    tools_response = client.post(f"/api/v1/labs/{lab_id}/tools", json={"name": "Splunk"})
    assert tools_response.status_code == 200

    # --- Add MITRE Technique -----------------------------------------------------------
    technique = next(t for t in client.get("/api/v1/mitre-techniques").json() if t["technique_id"] == "T1110")
    technique_response = client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={
            "technique_id": technique["id"],
            "justification": "Repeated failed logon attempts against a single account match this technique.",
        },
    )
    assert technique_response.status_code == 200
    assert technique_response.json()[0]["technique"]["technique_id"] == "T1110"

    # Confirm everything attached so far shows up together on the lab.
    fully_documented_lab = client.get(f"/api/v1/labs/{lab_id}").json()
    assert {s["name"] for s in fully_documented_lab["skills"]} == {"Log Analysis", "Threat Detection"}
    assert fully_documented_lab["tools"][0]["name"] == "Splunk"
    assert fully_documented_lab["techniques"][0]["technique"]["technique_id"] == "T1110"

    # --- Complete Lab -----------------------------------------------------------
    complete_response = client.patch(f"/api/v1/labs/{lab_id}/status", json={"status": "Completed"})
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "Completed"

    # Add the completion date a real workflow would set alongside marking it done.
    client.put(
        f"/api/v1/labs/{lab_id}",
        json={
            "title": lab["title"],
            "platform": lab["platform"],
            "category": lab["category"],
            "difficulty": lab["difficulty"],
            "status": "Completed",
            "date_started": "2026-03-01",
            "date_completed": "2026-03-01",
            "objective": lab["objective"],
        },
    )

    # This lab is now real, measurable activity: it should count in stats.
    overview = client.get("/api/v1/stats/overview").json()
    assert overview["labs_completed"] == 1
    assert overview["skills_practiced"] == 2
    assert overview["tools_used"] == 1
    assert overview["techniques_practiced"] == 1

    # --- Mark Portfolio Ready -----------------------------------------------------------
    # Evidence stays private by default even when the lab is published —
    # explicitly opt it in first, as a real user would from the UI.
    client.patch(f"/api/v1/evidence/{evidence_id}", json={"is_public": True})

    publish_response = client.patch(f"/api/v1/labs/{lab_id}/portfolio", json={"is_portfolio_ready": True})
    assert publish_response.status_code == 200
    published_lab = publish_response.json()
    assert published_lab["is_portfolio_ready"] is True
    slug = published_lab["portfolio_slug"]
    assert slug is not None

    # --- View Public Write-up -----------------------------------------------------------
    # No login for this part — simulate a visitor by using a fresh,
    # unauthenticated client (its own empty cookie jar) against the same
    # app and, since app.dependency_overrides is shared, the same
    # in-memory test database the authenticated client just wrote to.
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as public_visitor:
        index_response = public_visitor.get("/api/v1/public/portfolio")
        assert index_response.status_code == 200
        assert any(entry["slug"] == slug for entry in index_response.json())

        public_lab_response = public_visitor.get(f"/api/v1/public/portfolio/{slug}")
        assert public_lab_response.status_code == 200
        public_view = public_lab_response.json()

        # The public write-up shows what was documented...
        assert public_view["title"] == "Brute Force Detection Lab"
        assert "brute-force" in public_view["analysis"]
        assert "Log Analysis" in public_view["skills"]
        assert "Splunk" in public_view["tools"]
        assert public_view["techniques"][0]["technique_id"] == "T1110"
        assert len(public_view["evidence"]) == 1

        # ...but never the private Reflection field, regardless of how
        # thoroughly the lab was documented or published.
        assert "reflection" not in public_view
        assert "query filters" not in str(public_view)

        public_evidence_response = public_visitor.get(f"/api/v1/public/evidence/{evidence_id}/file")
        assert public_evidence_response.status_code == 200
        assert public_evidence_response.content == VALID_PNG_BYTES
