"""
Tests for Milestone 8: learning roadmap.

Covers: creating a tree of goals, linking a goal to a skill, rejecting
an invalid parent/skill reference, cycle prevention (a goal can't become
its own ancestor), progress computed from real lab activity for a
skill-linked goal, the simple children-rollup for a grouping goal,
cascading delete of sub-goals, and cross-user isolation.
"""

import pytest

from app.seed.seed_data import seed_skills_and_tools

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


@pytest.fixture()
def seeded(db_session):
    seed_skills_and_tools(db_session)
    return db_session


def _register(client):
    client.post("/api/v1/auth/register", json=VALID_USER)


def _skill_id(client, name: str) -> str:
    return next(s["id"] for s in client.get("/api/v1/skills").json() if s["name"] == name)


def test_create_root_goal(client):
    _register(client)
    response = client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"})
    assert response.status_code == 201
    assert response.json()["parent_goal_id"] is None


def test_create_child_goal(client):
    _register(client)
    parent = client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"}).json()
    child = client.post(
        "/api/v1/learning-goals", json={"title": "Networking", "parent_goal_id": parent["id"]}
    )
    assert child.status_code == 201
    assert child.json()["parent_goal_id"] == parent["id"]


def test_create_goal_rejects_nonexistent_parent(client):
    import uuid as uuid_module

    _register(client)
    response = client.post(
        "/api/v1/learning-goals", json={"title": "Orphan", "parent_goal_id": str(uuid_module.uuid4())}
    )
    assert response.status_code == 404


def test_create_goal_rejects_nonexistent_skill(client):
    import uuid as uuid_module

    _register(client)
    response = client.post(
        "/api/v1/learning-goals", json={"title": "SIEM", "related_skill_id": str(uuid_module.uuid4())}
    )
    assert response.status_code == 400


def test_create_goal_with_valid_related_skill(client, seeded):
    _register(client)
    skill_id = _skill_id(client, "SIEM")
    response = client.post("/api/v1/learning-goals", json={"title": "SIEM", "related_skill_id": skill_id})
    assert response.status_code == 201
    assert response.json()["related_skill_id"] == skill_id


def test_update_goal_rejects_self_as_parent(client):
    _register(client)
    goal = client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"}).json()
    response = client.put(
        f"/api/v1/learning-goals/{goal['id']}", json={"title": "SOC Analyst", "parent_goal_id": goal["id"]}
    )
    assert response.status_code == 400


def test_update_goal_rejects_descendant_as_parent(client):
    _register(client)
    root = client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"}).json()
    child = client.post(
        "/api/v1/learning-goals", json={"title": "Networking", "parent_goal_id": root["id"]}
    ).json()

    # Try to make root a child of its own child -> would create a cycle.
    response = client.put(
        f"/api/v1/learning-goals/{root['id']}", json={"title": "SOC Analyst", "parent_goal_id": child["id"]}
    )
    assert response.status_code == 400


def test_update_goal_allows_reparenting_to_unrelated_goal(client):
    _register(client)
    group_a = client.post("/api/v1/learning-goals", json={"title": "Group A"}).json()
    group_b = client.post("/api/v1/learning-goals", json={"title": "Group B"}).json()
    child = client.post(
        "/api/v1/learning-goals", json={"title": "Child", "parent_goal_id": group_a["id"]}
    ).json()

    response = client.put(
        f"/api/v1/learning-goals/{child['id']}", json={"title": "Child", "parent_goal_id": group_b["id"]}
    )
    assert response.status_code == 200
    assert response.json()["parent_goal_id"] == group_b["id"]


def test_delete_goal_cascades_to_children(client, db_session):
    from app.models.learning_goal import LearningGoal

    _register(client)
    root = client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"}).json()
    child = client.post(
        "/api/v1/learning-goals", json={"title": "Networking", "parent_goal_id": root["id"]}
    ).json()

    response = client.delete(f"/api/v1/learning-goals/{root['id']}")
    assert response.status_code == 204

    db_session.expire_all()
    assert db_session.query(LearningGoal).filter(LearningGoal.id == child["id"]).count() == 0


def test_progress_for_skill_linked_goal_with_no_activity(client, seeded):
    _register(client)
    skill_id = _skill_id(client, "SIEM")
    goal = client.post("/api/v1/learning-goals", json={"title": "SIEM", "related_skill_id": skill_id}).json()

    progress = client.get(f"/api/v1/learning-goals/{goal['id']}/progress").json()
    assert progress["has_related_skill"] is True
    assert progress["labs_completed"] == 0
    assert "first lab" in progress["recommended_next_activity"]


def test_progress_reflects_real_lab_activity(client, seeded):
    _register(client)
    skill_id = _skill_id(client, "SIEM")
    goal = client.post("/api/v1/learning-goals", json={"title": "SIEM", "related_skill_id": skill_id}).json()

    lab = client.post("/api/v1/labs", json=BASE_LAB).json()
    client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "SIEM"})

    progress = client.get(f"/api/v1/learning-goals/{goal['id']}/progress").json()
    assert progress["labs_completed"] == 1
    assert len(progress["related_labs"]) == 1
    assert progress["related_labs"][0]["title"] == BASE_LAB["title"]


def test_progress_excludes_planned_labs(client, seeded):
    _register(client)
    skill_id = _skill_id(client, "SIEM")
    goal = client.post("/api/v1/learning-goals", json={"title": "SIEM", "related_skill_id": skill_id}).json()

    lab = client.post("/api/v1/labs", json={**BASE_LAB, "status": "Planned"}).json()
    client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "SIEM"})

    progress = client.get(f"/api/v1/learning-goals/{goal['id']}/progress").json()
    assert progress["labs_completed"] == 0


def test_progress_includes_related_ctf_challenges(client, seeded):
    _register(client)
    skill_id = _skill_id(client, "Cryptography")
    goal = client.post(
        "/api/v1/learning-goals", json={"title": "Cryptography", "related_skill_id": skill_id}
    ).json()

    event = client.post("/api/v1/ctf-events", json={"name": "PicoCTF"}).json()
    challenge = client.post(
        f"/api/v1/ctf-events/{event['id']}/challenges",
        json={"title": "RSA Basics", "category": "Crypto", "difficulty": "Easy", "status": "Solved"},
    ).json()
    client.post(f"/api/v1/ctf-challenges/{challenge['id']}/skills", json={"name": "Cryptography"})

    progress = client.get(f"/api/v1/learning-goals/{goal['id']}/progress").json()
    assert len(progress["related_ctf_challenges"]) == 1
    assert progress["related_ctf_challenges"][0]["title"] == "RSA Basics"


def test_progress_for_grouping_goal_with_no_children(client):
    _register(client)
    goal = client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"}).json()

    progress = client.get(f"/api/v1/learning-goals/{goal['id']}/progress").json()
    assert progress["has_related_skill"] is False
    assert progress["child_count"] == 0
    assert "sub-goal" in progress["recommended_next_activity"]


def test_progress_for_grouping_goal_rolls_up_children(client, seeded):
    _register(client)
    root = client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"}).json()

    siem_skill_id = _skill_id(client, "SIEM")
    linux_skill_id = _skill_id(client, "Linux")
    client.post(
        "/api/v1/learning-goals",
        json={"title": "SIEM", "parent_goal_id": root["id"], "related_skill_id": siem_skill_id},
    )
    client.post(
        "/api/v1/learning-goals",
        json={"title": "Linux", "parent_goal_id": root["id"], "related_skill_id": linux_skill_id},
    )

    # No activity yet on either sub-goal.
    progress = client.get(f"/api/v1/learning-goals/{root['id']}/progress").json()
    assert progress["child_count"] == 2
    assert progress["children_with_activity"] == 0

    # Practice one of them.
    lab = client.post("/api/v1/labs", json=BASE_LAB).json()
    client.post(f"/api/v1/labs/{lab['id']}/skills", json={"name": "Linux"})

    progress = client.get(f"/api/v1/learning-goals/{root['id']}/progress").json()
    assert progress["children_with_activity"] == 1
    assert "1 of 2" in progress["recommended_next_activity"]


def test_list_goals_only_returns_own(client):
    _register(client)
    client.post("/api/v1/learning-goals", json={"title": "SOC Analyst"})
    client.post("/api/v1/learning-goals", json={"title": "Penetration Tester"})

    response = client.get("/api/v1/learning-goals")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_user_cannot_access_another_users_goal(client, db_session):
    from app.models.learning_goal import LearningGoal
    from app.models.user import User
    from app.security import hash_password

    _register(client)
    other_user = User(email="other@example.com", display_name="Other", password_hash=hash_password("anotherpass9"))
    db_session.add(other_user)
    db_session.flush()
    other_goal = LearningGoal(user_id=other_user.id, title="Private Goal")
    db_session.add(other_goal)
    db_session.commit()
    db_session.refresh(other_goal)

    response = client.get(f"/api/v1/learning-goals/{other_goal.id}/progress")
    assert response.status_code == 404


def test_roadmap_endpoints_require_authentication(client):
    assert client.get("/api/v1/learning-goals").status_code == 401
