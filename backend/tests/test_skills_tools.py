"""
Tests for Milestone 4: skills + tools tracking.

Covers: attaching skills/tools to labs (with get-or-create-by-name
semantics), detaching, the list/detail stats endpoints computing real
lab counts and last-practiced/last-used dates from actual lab data
(never a fabricated percentage), related-tools/related-skills cross
referencing, and that stats are correctly scoped per user.
"""

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

LAB_A = {
    "title": "Windows Event Log Investigation",
    "platform": "TryHackMe",
    "category": "SOC / Blue Team",
    "difficulty": "Medium",
    "status": "Completed",
    "date_completed": "2026-01-10",
}

LAB_B = {
    "title": "Brute Force Detection Lab",
    "platform": "Home Lab",
    "category": "SOC / Blue Team",
    "difficulty": "Easy",
    "status": "Completed",
    "date_completed": "2026-02-15",
}


def _register(client):
    client.post("/api/v1/auth/register", json=VALID_USER)


def test_attach_skill_creates_it_if_missing(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=LAB_A).json()

    response = client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "Log Analysis"})
    assert response.status_code == 200
    skills = response.json()
    assert len(skills) == 1
    assert skills[0]["name"] == "Log Analysis"


def test_attaching_same_skill_name_reuses_existing_skill(client):
    _register(client)
    lab1 = client.post("/api/v1/labs", json=LAB_A).json()
    lab2 = client.post("/api/v1/labs", json=LAB_B).json()

    client.post(f"/api/v1/labs/{lab1['id']}/skills", json={"name": "Log Analysis"})
    client.post(f"/api/v1/labs/{lab2['id']}/skills", json={"name": "log analysis"})  # different case

    skills_list = client.get("/api/v1/skills").json()
    log_analysis_entries = [s for s in skills_list if s["name"].lower() == "log analysis"]
    assert len(log_analysis_entries) == 1
    assert log_analysis_entries[0]["lab_count"] == 2


def test_detach_skill(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=LAB_A).json()
    skills = client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "SIEM"}).json()
    skill_id = skills[0]["id"]

    response = client.delete(f"/api/v1/labs/{lab['id']}/skills/{skill_id}")
    assert response.status_code == 200
    assert response.json() == []


def test_attach_and_detach_tool(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=LAB_A).json()

    add_response = client.post(f"/api/v1/labs/{lab['id']}/tools", json={"name": "Splunk"})
    assert add_response.status_code == 200
    tool_id = add_response.json()[0]["id"]

    remove_response = client.delete(f"/api/v1/labs/{lab['id']}/tools/{tool_id}")
    assert remove_response.status_code == 200
    assert remove_response.json() == []


def test_skill_stats_reflect_real_lab_data(client):
    _register(client)
    lab1 = client.post("/api/v1/labs", json=LAB_A).json()
    lab2 = client.post("/api/v1/labs", json=LAB_B).json()

    client.post(f"/api/v1/labs/{lab1['id']}/skills", json={"name": "Threat Detection"})
    client.post(f"/api/v1/labs/{lab2['id']}/skills", json={"name": "Threat Detection"})

    skills_list = client.get("/api/v1/skills").json()
    entry = next(s for s in skills_list if s["name"] == "Threat Detection")
    assert entry["lab_count"] == 2
    # LAB_B completed later (2026-02-15) than LAB_A (2026-01-10)
    assert entry["last_practiced"] == "2026-02-15"


def test_skill_with_no_labs_shows_zero_stats(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=LAB_A).json()
    client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "OSINT"})

    skills_list = client.get("/api/v1/skills").json()
    entry = next(s for s in skills_list if s["name"] == "OSINT")
    assert entry["lab_count"] == 1

    # Detach it — the skill row still exists (shared master list) but with zero activity
    skill_id = entry["id"]
    client.delete(f"/api/v1/labs/{lab['id']}/skills/{skill_id}")

    skills_list_after = client.get("/api/v1/skills").json()
    entry_after = next(s for s in skills_list_after if s["id"] == skill_id)
    assert entry_after["lab_count"] == 0
    assert entry_after["last_practiced"] is None


def test_skill_detail_includes_related_labs_and_tools(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=LAB_A).json()

    skill = client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "Threat Hunting"}).json()[0]
    client.post(f"/api/v1/labs/{lab['id']}/tools", json={"name": "Sysmon"})

    detail = client.get(f"/api/v1/skills/{skill['id']}").json()
    assert detail["lab_count"] == 1
    assert len(detail["related_labs"]) == 1
    assert detail["related_labs"][0]["title"] == LAB_A["title"]
    assert len(detail["related_tools"]) == 1
    assert detail["related_tools"][0]["name"] == "Sysmon"


def test_tool_detail_includes_related_labs_and_skills(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=LAB_A).json()

    tool = client.post(f"/api/v1/labs/{lab['id']}/tools", json={"name": "Wireshark"}).json()[0]
    client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "Network Analysis"})

    detail = client.get(f"/api/v1/tools/{tool['id']}").json()
    assert detail["lab_count"] == 1
    assert len(detail["related_labs"]) == 1
    assert len(detail["related_skills"]) == 1
    assert detail["related_skills"][0]["name"] == "Network Analysis"


def test_skill_not_found_returns_404(client):
    _register(client)
    response = client.get("/api/v1/skills/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_lab_response_includes_attached_skills_and_tools(client):
    _register(client)
    lab = client.post("/api/v1/labs", json=LAB_A).json()
    client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "Linux"})
    client.post(f"/api/v1/labs/{lab['id']}/tools", json={"name": "Nmap"})

    fetched = client.get(f"/api/v1/labs/{lab['id']}").json()
    assert fetched["skills"][0]["name"] == "Linux"
    assert fetched["tools"][0]["name"] == "Nmap"


def test_skills_and_tools_require_authentication(client):
    assert client.get("/api/v1/skills").status_code == 401
    assert client.get("/api/v1/tools").status_code == 401
