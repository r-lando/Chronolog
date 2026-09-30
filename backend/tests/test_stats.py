"""
Tests for Milestone 7: dashboard + analytics.

The key property under test: every statistic is computed from stored
records with an explicit, consistent definition — "practiced" excludes
Planned labs everywhere (dashboard, Skills, MITRE), Partially Solved CTF
challenges don't count as solved, and completed labs without a date are
reported rather than silently dropped.
"""

from datetime import date, timedelta

import pytest

from app.seed.seed_data import seed_skills_and_tools
from app.services.stats_service import compute_streak

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}

BASE_LAB = {
    "title": "Sample Lab",
    "platform": "TryHackMe",
    "category": "SOC / Blue Team",
    "difficulty": "Easy",
    "status": "Completed",
}

TODAY = date.today()


@pytest.fixture()
def seeded(db_session):
    seed_skills_and_tools(db_session)
    return db_session


def _register(client):
    client.post("/api/v1/auth/register", json=VALID_USER)


def _lab(client, **overrides) -> dict:
    response = client.post("/api/v1/labs", json={**BASE_LAB, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def _attach(client, lab_id: str, skills=(), tools=()):
    for name in skills:
        client.post(f"/api/v1/labs/{lab_id}/skills", json={"name": name})
    for name in tools:
        client.post(f"/api/v1/labs/{lab_id}/tools", json={"name": name})


def _technique(client, code: str) -> dict:
    return next(t for t in client.get("/api/v1/mitre-techniques").json() if t["technique_id"] == code)


def _map_technique(client, lab_id: str, code: str):
    technique = _technique(client, code)
    response = client.post(
        f"/api/v1/labs/{lab_id}/techniques",
        json={"technique_id": technique["id"], "justification": "Observed this behavior during the lab."},
    )
    assert response.status_code == 200, response.text


# ---- streak logic (pure function, no database) --------------------------------


def test_streak_empty_is_zero():
    assert compute_streak(set(), TODAY) == 0


def test_streak_today_only():
    assert compute_streak({TODAY}, TODAY) == 1


def test_streak_consecutive_days_ending_today():
    days = {TODAY, TODAY - timedelta(days=1), TODAY - timedelta(days=2)}
    assert compute_streak(days, TODAY) == 3


def test_streak_stays_alive_if_last_activity_was_yesterday():
    days = {TODAY - timedelta(days=1), TODAY - timedelta(days=2)}
    assert compute_streak(days, TODAY) == 2


def test_streak_broken_if_last_activity_was_two_days_ago():
    assert compute_streak({TODAY - timedelta(days=2)}, TODAY) == 0


def test_streak_stops_at_first_gap():
    days = {TODAY, TODAY - timedelta(days=1), TODAY - timedelta(days=3)}
    assert compute_streak(days, TODAY) == 2


def test_streak_ignores_future_dates():
    assert compute_streak({TODAY + timedelta(days=1)}, TODAY) == 0
    assert compute_streak({TODAY, TODAY + timedelta(days=5)}, TODAY) == 1


# ---- overview -------------------------------------------------------------------


def test_overview_is_all_zeros_for_a_new_account(client):
    _register(client)
    body = client.get("/api/v1/stats/overview").json()
    assert body == {
        "labs_completed": 0,
        "ctf_challenges_solved": 0,
        "total_learning_hours": 0.0,
        "current_streak_days": 0,
        "skills_practiced": 0,
        "tools_used": 0,
        "techniques_practiced": 0,
        "labs_completed_this_month": 0,
        "completed_labs_without_date": 0,
    }


def test_overview_counts_real_data_and_excludes_planned_labs(client, seeded):
    _register(client)

    completed = _lab(
        client,
        title="Completed Lab",
        status="Completed",
        date_started=(TODAY - timedelta(days=2)).isoformat(),
        date_completed=TODAY.isoformat(),
        time_spent_minutes=90,
    )
    _attach(client, completed["id"], skills=["Log Analysis"], tools=["Wireshark"])
    _map_technique(client, completed["id"], "T1110")

    in_progress = _lab(
        client,
        title="In Progress Lab",
        status="In Progress",
        date_started=(TODAY - timedelta(days=1)).isoformat(),
        time_spent_minutes=30,
    )
    _attach(client, in_progress["id"], skills=["Log Analysis", "SIEM"])

    planned = _lab(client, title="Planned Lab", status="Planned")
    _attach(client, planned["id"], skills=["Malware Analysis"], tools=["Nmap"])
    _map_technique(client, planned["id"], "T1566")

    event = client.post(
        "/api/v1/ctf-events", json={"name": "PicoCTF", "event_date": TODAY.isoformat()}
    ).json()
    for title, status, minutes in [
        ("Solved One", "Solved", 60),
        ("Partial One", "Partially Solved", 30),
        ("Unsolved One", "Unsolved", None),
    ]:
        client.post(
            f"/api/v1/ctf-events/{event['id']}/challenges",
            json={
                "title": title,
                "category": "Web",
                "difficulty": "Easy",
                "status": status,
                "time_spent_minutes": minutes,
            },
        )

    body = client.get("/api/v1/stats/overview").json()

    assert body["labs_completed"] == 1
    assert body["ctf_challenges_solved"] == 1  # Partially Solved does not count
    assert body["total_learning_hours"] == 3.5  # (90 + 30 + 60 + 30) / 60
    # Activity days: today-2 (start), yesterday (start), today (complete + CTF)
    assert body["current_streak_days"] == 3
    assert body["skills_practiced"] == 2  # Log Analysis + SIEM; Malware Analysis is Planned-only
    assert body["tools_used"] == 1  # Wireshark; Nmap is Planned-only
    assert body["techniques_practiced"] == 1  # T1110; T1566 is on a Planned lab
    assert body["labs_completed_this_month"] == 1
    assert body["completed_labs_without_date"] == 0


def test_completed_lab_without_date_is_reported_not_silently_dropped(client):
    _register(client)
    _lab(client, title="Undated Completed Lab", status="Completed")  # no date_completed

    body = client.get("/api/v1/stats/overview").json()
    assert body["labs_completed"] == 1
    assert body["labs_completed_this_month"] == 0
    assert body["completed_labs_without_date"] == 1


def test_labs_completed_this_month_excludes_older_completions(client):
    _register(client)
    _lab(client, title="Old Lab", status="Completed", date_completed=(TODAY - timedelta(days=400)).isoformat())
    _lab(client, title="New Lab", status="Completed", date_completed=TODAY.isoformat())

    body = client.get("/api/v1/stats/overview").json()
    assert body["labs_completed"] == 2
    assert body["labs_completed_this_month"] == 1


# ---- chart breakdowns -------------------------------------------------------------


def test_labs_by_category_excludes_planned(client):
    _register(client)
    _lab(client, title="A", category="Web Security")
    _lab(client, title="B", category="Web Security", status="In Progress")
    _lab(client, title="C", category="Linux")
    _lab(client, title="D", category="Cloud Security", status="Planned")

    points = client.get("/api/v1/stats/labs-by-category").json()
    assert points == [
        {"label": "Web Security", "count": 2},
        {"label": "Linux", "count": 1},
    ]


def test_difficulty_distribution_is_ordered_and_includes_zeroes(client):
    _register(client)
    _lab(client, title="A", difficulty="Easy")
    _lab(client, title="B", difficulty="Hard")
    _lab(client, title="C", difficulty="Hard")

    points = client.get("/api/v1/stats/difficulty-distribution").json()
    assert [p["label"] for p in points] == ["Beginner", "Easy", "Medium", "Hard", "Expert"]
    assert [p["count"] for p in points] == [0, 1, 0, 2, 0]


def test_activity_timeline_is_zero_filled_and_bucketed_by_completion_month(client):
    _register(client)
    _lab(client, title="This Month", status="Completed", date_completed=TODAY.isoformat())
    _lab(client, title="This Month 2", status="Completed", date_completed=TODAY.isoformat())
    previous_month_day = TODAY.replace(day=1) - timedelta(days=1)
    _lab(client, title="Last Month", status="Completed", date_completed=previous_month_day.isoformat())
    _lab(client, title="Way Too Old", status="Completed", date_completed=(TODAY - timedelta(days=800)).isoformat())
    _lab(client, title="Not Completed", status="In Progress", date_started=TODAY.isoformat())

    points = client.get("/api/v1/stats/activity-timeline").json()
    assert len(points) == 12

    by_label = {p["label"]: p["count"] for p in points}
    assert by_label[f"{TODAY.year:04d}-{TODAY.month:02d}"] == 2
    assert by_label[f"{previous_month_day.year:04d}-{previous_month_day.month:02d}"] == 1
    assert sum(by_label.values()) == 3  # the 800-day-old lab falls outside the 12-month window
    assert points[-1]["label"] == f"{TODAY.year:04d}-{TODAY.month:02d}"  # chronological, ending this month


def test_skills_practiced_sorted_by_lab_count_and_excludes_planned(client):
    _register(client)
    lab1 = _lab(client, title="One")
    lab2 = _lab(client, title="Two")
    planned = _lab(client, title="Three", status="Planned")
    _attach(client, lab1["id"], skills=["Log Analysis", "SIEM"])
    _attach(client, lab2["id"], skills=["Log Analysis"])
    _attach(client, planned["id"], skills=["Malware Analysis"])

    points = client.get("/api/v1/stats/skills-practiced").json()
    assert points == [
        {"label": "Log Analysis", "count": 2},
        {"label": "SIEM", "count": 1},
    ]


def test_tools_used(client):
    _register(client)
    lab1 = _lab(client, title="One")
    lab2 = _lab(client, title="Two")
    _attach(client, lab1["id"], tools=["Wireshark", "Nmap"])
    _attach(client, lab2["id"], tools=["Wireshark"])

    points = client.get("/api/v1/stats/tools-used").json()
    assert points[0] == {"label": "Wireshark", "count": 2}
    assert {"label": "Nmap", "count": 1} in points


def test_mitre_coverage_counts_distinct_techniques_per_tactic(client, seeded):
    _register(client)
    lab1 = _lab(client, title="One")
    lab2 = _lab(client, title="Two")
    planned = _lab(client, title="Planned", status="Planned")

    _map_technique(client, lab1["id"], "T1110")  # Credential Access
    _map_technique(client, lab2["id"], "T1110")  # same technique again: still counts once
    _map_technique(client, lab1["id"], "T1003")  # Credential Access
    _map_technique(client, lab2["id"], "T1078")  # Defense Evasion
    _map_technique(client, planned["id"], "T1566")  # Initial Access, but Planned-only

    points = client.get("/api/v1/stats/mitre-coverage").json()
    assert points == [
        {"label": "Credential Access", "count": 2},
        {"label": "Defense Evasion", "count": 1},
    ]


# ---- recent activity ---------------------------------------------------------------


def test_recent_activity_is_limited_and_newest_first(client):
    _register(client)
    for i in range(7):
        _lab(client, title=f"Lab {i}")

    recent = client.get("/api/v1/stats/recent").json()
    assert len(recent["recent_labs"]) == 5
    assert recent["recent_labs"][0]["title"] == "Lab 6"


def test_recent_activity_includes_ctf_challenges_with_event_name(client):
    _register(client)
    event = client.post("/api/v1/ctf-events", json={"name": "HTB Cyber Apocalypse"}).json()
    client.post(
        f"/api/v1/ctf-events/{event['id']}/challenges",
        json={"title": "Some Challenge", "category": "Crypto", "difficulty": "Medium", "status": "Solved"},
    )

    recent = client.get("/api/v1/stats/recent").json()
    assert len(recent["recent_ctf_challenges"]) == 1
    assert recent["recent_ctf_challenges"][0]["event_name"] == "HTB Cyber Apocalypse"


def test_recently_practiced_skills_excludes_planned_only_skills(client):
    _register(client)
    done = _lab(client, title="Done", date_completed=TODAY.isoformat())
    planned = _lab(client, title="Planned", status="Planned")
    _attach(client, done["id"], skills=["Threat Hunting"])
    _attach(client, planned["id"], skills=["Cryptography"])

    recent = client.get("/api/v1/stats/recent").json()
    names = [s["name"] for s in recent["recently_practiced_skills"]]
    assert names == ["Threat Hunting"]


# ---- consistency across pages -----------------------------------------------------


def test_skills_and_mitre_pages_apply_the_same_planned_rule_as_the_dashboard(client, seeded):
    _register(client)
    planned = _lab(client, title="Planned", status="Planned")
    _attach(client, planned["id"], skills=["Malware Analysis"], tools=["Nmap"])
    _map_technique(client, planned["id"], "T1566")

    skill = next(s for s in client.get("/api/v1/skills").json() if s["name"] == "Malware Analysis")
    tool = next(t for t in client.get("/api/v1/tools").json() if t["name"] == "Nmap")
    assert skill["lab_count"] == 0
    assert tool["lab_count"] == 0
    assert _technique(client, "T1566")["lab_count"] == 0

    # Moving the lab to In Progress makes the very same data count everywhere.
    client.patch(f"/api/v1/labs/{planned['id']}/status", json={"status": "In Progress"})
    skill = next(s for s in client.get("/api/v1/skills").json() if s["name"] == "Malware Analysis")
    assert skill["lab_count"] == 1
    assert client.get("/api/v1/stats/overview").json()["skills_practiced"] == 1


# ---- isolation + auth ----------------------------------------------------------------


def test_other_users_data_is_never_counted(client, db_session):
    from app.models.lab import Lab
    from app.models.user import User
    from app.security import hash_password

    _register(client)
    other = User(email="other@example.com", display_name="Other", password_hash=hash_password("anotherpass9"))
    db_session.add(other)
    db_session.flush()
    db_session.add(
        Lab(
            user_id=other.id,
            title="Someone Else's Lab",
            category="Linux",
            difficulty="Easy",
            status="Completed",
            date_completed=TODAY,
            time_spent_minutes=600,
        )
    )
    db_session.commit()

    body = client.get("/api/v1/stats/overview").json()
    assert body["labs_completed"] == 0
    assert body["total_learning_hours"] == 0.0
    assert client.get("/api/v1/stats/labs-by-category").json() == []


@pytest.mark.parametrize(
    "path",
    [
        "overview",
        "labs-by-category",
        "difficulty-distribution",
        "activity-timeline",
        "skills-practiced",
        "tools-used",
        "mitre-coverage",
        "recent",
    ],
)
def test_stats_endpoints_require_authentication(client, path):
    assert client.get(f"/api/v1/stats/{path}").status_code == 401
