"""
Tests for Milestone 11: sample data seeding.

The sample labs/CTF challenges/roadmap reference skills, tools, and
MITRE techniques by exact name/code (e.g. "Threat Hunting", "T1110").
Those references are plain string lookups in seed_data.py with no
validation at insert time — a typo would silently produce a lab with no
skills attached instead of an error. These tests catch that class of
mistake by asserting every expected cross-reference actually resolved.
"""

import pytest

from app.models.ctf import CtfChallenge, CtfEvent
from app.models.lab import Lab
from app.models.learning_goal import LearningGoal
from app.seed.seed_data import (
    SAMPLE_CTF_CHALLENGES,
    SAMPLE_LABS,
    SAMPLE_ROADMAP,
    seed_sample_ctf,
    seed_sample_labs,
    seed_sample_roadmap,
    seed_skills_and_tools,
)

VALID_USER = {
    "email": "analyst@example.com",
    "display_name": "SOC Analyst",
    "password": "correcthorse9",
}


@pytest.fixture()
def registered_user_id(client, db_session):
    from app.models.user import User

    client.post("/api/v1/auth/register", json=VALID_USER)
    return db_session.query(User).filter(User.email == VALID_USER["email"]).first().id


def test_sample_labs_cover_all_expected_categories_and_statuses(client, db_session, registered_user_id):
    seed_skills_and_tools(db_session)
    created = seed_sample_labs(db_session, registered_user_id)
    assert created == len(SAMPLE_LABS)

    labs = db_session.query(Lab).filter(Lab.user_id == registered_user_id).all()
    assert len(labs) == 10

    statuses = {lab.status for lab in labs}
    assert "Completed" in statuses
    assert "In Progress" in statuses
    assert "Planned" in statuses  # demonstrates the "not yet practiced" exclusion rule has real sample data to show


def test_every_sample_lab_has_a_writeup_shell(client, db_session, registered_user_id):
    seed_skills_and_tools(db_session)
    seed_sample_labs(db_session, registered_user_id)

    labs = db_session.query(Lab).filter(Lab.user_id == registered_user_id).all()
    assert all(lab.writeup is not None for lab in labs)


def test_sample_lab_skill_references_all_resolve(client, db_session, registered_user_id):
    """Every skill name referenced in SAMPLE_LABS must exist in SKILLS — a mismatch would silently attach nothing."""
    seed_skills_and_tools(db_session)
    seed_sample_labs(db_session, registered_user_id)

    labs = db_session.query(Lab).filter(Lab.user_id == registered_user_id).all()
    labs_by_title = {lab.title: lab for lab in labs}

    for entry in SAMPLE_LABS:
        lab = labs_by_title[entry["title"]]
        actual_skill_names = {s.name for s in lab.skills}
        assert actual_skill_names == set(entry["skills"]), f"Skill mismatch on '{entry['title']}'"


def test_sample_lab_tool_references_all_resolve(client, db_session, registered_user_id):
    seed_skills_and_tools(db_session)
    seed_sample_labs(db_session, registered_user_id)

    labs = db_session.query(Lab).filter(Lab.user_id == registered_user_id).all()
    labs_by_title = {lab.title: lab for lab in labs}

    for entry in SAMPLE_LABS:
        lab = labs_by_title[entry["title"]]
        actual_tool_names = {t.name for t in lab.tools}
        assert actual_tool_names == set(entry["tools"]), f"Tool mismatch on '{entry['title']}'"


def test_sample_lab_technique_references_all_resolve(client, db_session, registered_user_id):
    seed_skills_and_tools(db_session)
    seed_sample_labs(db_session, registered_user_id)

    labs = db_session.query(Lab).filter(Lab.user_id == registered_user_id).all()
    labs_by_title = {lab.title: lab for lab in labs}

    expected_with_technique = [e for e in SAMPLE_LABS if e["technique"]]
    assert len(expected_with_technique) > 0  # sanity: the fixture data actually exercises this path

    for entry in expected_with_technique:
        lab = labs_by_title[entry["title"]]
        assert len(lab.techniques) == 1, f"Expected one technique on '{entry['title']}'"
        assert lab.techniques[0].technique.technique_id == entry["technique"]


def test_seed_sample_labs_is_idempotent(client, db_session, registered_user_id):
    seed_skills_and_tools(db_session)
    first_run = seed_sample_labs(db_session, registered_user_id)
    second_run = seed_sample_labs(db_session, registered_user_id)
    assert first_run == len(SAMPLE_LABS)
    assert second_run == 0

    total_labs = db_session.query(Lab).filter(Lab.user_id == registered_user_id).count()
    assert total_labs == len(SAMPLE_LABS)  # not doubled


def test_sample_labs_pass_the_same_api_validation_as_real_data(client, db_session, registered_user_id):
    """
    The seed script writes directly via the ORM, bypassing the Pydantic
    validators in app/schemas/lab.py (controlled vocabulary checks for
    category/difficulty/status). This test re-validates every seeded
    lab against those exact schemas to catch any category/difficulty/
    status typo in the sample data that direct ORM insertion wouldn't.
    """
    from app.schemas.lab import LabCreate

    seed_skills_and_tools(db_session)
    seed_sample_labs(db_session, registered_user_id)

    for entry in SAMPLE_LABS:
        LabCreate(
            title=entry["title"],
            platform=entry["platform"],
            category=entry["category"],
            difficulty=entry["difficulty"],
            status=entry["status"],
            date_started=entry["date_started"],
            date_completed=entry["date_completed"],
            time_spent_minutes=entry["time_spent_minutes"],
            description=None,
            objective=entry["objective"],
            environment=entry["environment"],
        )  # raises if any value violates the real API's validation rules


def test_sample_ctf_challenges_created_under_one_event(client, db_session, registered_user_id):
    created = seed_sample_ctf(db_session, registered_user_id)
    assert created == len(SAMPLE_CTF_CHALLENGES)

    event = db_session.query(CtfEvent).filter(CtfEvent.user_id == registered_user_id).first()
    assert event is not None
    challenges = db_session.query(CtfChallenge).filter(CtfChallenge.ctf_event_id == event.id).all()
    assert len(challenges) == len(SAMPLE_CTF_CHALLENGES)

    statuses = {c.status for c in challenges}
    assert statuses == {"Solved", "Partially Solved", "Unsolved"}


def test_sample_ctf_challenges_pass_the_same_api_validation_as_real_data(client, db_session, registered_user_id):
    from app.schemas.ctf import CtfChallengeCreate

    for entry in SAMPLE_CTF_CHALLENGES:
        CtfChallengeCreate(**entry)


def test_seed_sample_ctf_is_idempotent(client, db_session, registered_user_id):
    first_run = seed_sample_ctf(db_session, registered_user_id)
    second_run = seed_sample_ctf(db_session, registered_user_id)
    assert first_run == len(SAMPLE_CTF_CHALLENGES)
    assert second_run == 0


def test_sample_roadmap_matches_spec_structure(client, db_session, registered_user_id):
    seed_skills_and_tools(db_session)
    seed_sample_roadmap(db_session, registered_user_id)

    root = (
        db_session.query(LearningGoal)
        .filter(LearningGoal.user_id == registered_user_id, LearningGoal.parent_goal_id.is_(None))
        .first()
    )
    assert root.title == "SOC Analyst"

    children = db_session.query(LearningGoal).filter(LearningGoal.parent_goal_id == root.id).all()
    assert len(children) == len(SAMPLE_ROADMAP["children"])
    child_titles = {c.title for c in children}
    assert child_titles == {c["title"] for c in SAMPLE_ROADMAP["children"]}

    # Goals explicitly tied to a skill in the spec data should actually have that link.
    linked = {c.title: c.related_skill_id for c in children if c.related_skill_id is not None}
    assert "Linux" in linked
    assert "SIEM" in linked


def test_seed_sample_roadmap_is_idempotent(client, db_session, registered_user_id):
    seed_skills_and_tools(db_session)
    first_run = seed_sample_roadmap(db_session, registered_user_id)
    second_run = seed_sample_roadmap(db_session, registered_user_id)
    assert first_run > 0
    assert second_run == 0
