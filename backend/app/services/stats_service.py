"""
Dashboard statistics.

Every figure here is derived from stored lab / CTF records at request
time. Nothing is cached, seeded, or estimated, which is what the spec
means by "do not create meaningless fake percentages".

Definitions (kept explicit so the numbers are defensible in an
interview):
- "Practiced" lab: any lab whose status is not "Planned"
  (see app/services/activity.py).
- "Labs completed": status == "Completed".
- "CTF challenges solved": status == "Solved" (Partially Solved does not
  count as completed).
- "Learning hours": total time_spent_minutes across all labs and CTF
  challenges, converted to hours.
- "Activity day" (for the streak): a day on which a practiced lab was
  started or completed, or a CTF challenge was logged (the event's date
  if set, otherwise the day the challenge record was created).
- Today is passed in rather than read inside each function, so tests can
  pin the date and the streak logic is deterministic.
"""

import uuid
from collections import Counter
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.constants import LAB_DIFFICULTIES
from app.models.ctf import CtfChallenge, CtfEvent
from app.models.lab import Lab
from app.services.activity import is_practiced
from app.services.skill_tool_service import list_skills_with_stats

TIMELINE_MONTHS = 12
RECENT_LIMIT = 5
TOP_N = 10


# ---- data loading ---------------------------------------------------------


def _user_labs(db: Session, user_id: uuid.UUID) -> list[Lab]:
    return db.query(Lab).filter(Lab.user_id == user_id).all()


def _user_challenges(db: Session, user_id: uuid.UUID) -> list[CtfChallenge]:
    return (
        db.query(CtfChallenge)
        .join(CtfEvent, CtfChallenge.ctf_event_id == CtfEvent.id)
        .filter(CtfEvent.user_id == user_id)
        .all()
    )


def _to_points(counter: Counter, limit: int | None = None) -> list[dict]:
    # Sort by count (desc), then label, so equal counts have a stable order.
    ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    if limit is not None:
        ordered = ordered[:limit]
    return [{"label": label, "count": count} for label, count in ordered]


# ---- streak ---------------------------------------------------------------


def compute_streak(activity_days: set[date], today: date) -> int:
    """
    Consecutive days of activity ending today. If there's no activity today
    yet but there was yesterday, the streak is still alive (you haven't
    had the chance to break it today) and counts back from yesterday.
    Future-dated entries are ignored.
    """
    days = {d for d in activity_days if d <= today}
    if not days:
        return 0

    if today in days:
        cursor = today
    elif (today - timedelta(days=1)) in days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _activity_days(labs: list[Lab], challenges: list[CtfChallenge]) -> set[date]:
    days: set[date] = set()
    for lab in labs:
        if not is_practiced(lab):
            continue
        if lab.date_started:
            days.add(lab.date_started)
        if lab.date_completed:
            days.add(lab.date_completed)
    for challenge in challenges:
        days.add(challenge.event.event_date or challenge.created_at.date())
    return days


# ---- overview ---------------------------------------------------------------


def get_overview(db: Session, user_id: uuid.UUID, today: date) -> dict:
    labs = _user_labs(db, user_id)
    challenges = _user_challenges(db, user_id)
    practiced = [lab for lab in labs if is_practiced(lab)]
    completed = [lab for lab in labs if lab.status == "Completed"]

    total_minutes = sum(lab.time_spent_minutes or 0 for lab in labs) + sum(
        c.time_spent_minutes or 0 for c in challenges
    )

    return {
        "labs_completed": len(completed),
        "ctf_challenges_solved": sum(1 for c in challenges if c.status == "Solved"),
        "total_learning_hours": round(total_minutes / 60, 1),
        "current_streak_days": compute_streak(_activity_days(labs, challenges), today),
        "skills_practiced": len({skill.id for lab in practiced for skill in lab.skills}),
        "tools_used": len({tool.id for lab in practiced for tool in lab.tools}),
        "techniques_practiced": len({lt.technique_id for lab in practiced for lt in lab.techniques}),
        "labs_completed_this_month": sum(
            1
            for lab in completed
            if lab.date_completed
            and (lab.date_completed.year, lab.date_completed.month) == (today.year, today.month)
        ),
        "completed_labs_without_date": sum(1 for lab in completed if lab.date_completed is None),
    }


# ---- chart breakdowns ---------------------------------------------------------


def labs_by_category(db: Session, user_id: uuid.UUID) -> list[dict]:
    practiced = [lab for lab in _user_labs(db, user_id) if is_practiced(lab)]
    return _to_points(Counter(lab.category for lab in practiced))


def difficulty_distribution(db: Session, user_id: uuid.UUID) -> list[dict]:
    practiced = [lab for lab in _user_labs(db, user_id) if is_practiced(lab)]
    counts = Counter(lab.difficulty for lab in practiced)
    # Fixed easiest-to-hardest order, including real zeroes, so the chart
    # always reads as a distribution rather than a shuffled list.
    return [{"label": difficulty, "count": counts.get(difficulty, 0)} for difficulty in LAB_DIFFICULTIES]


def _last_n_months(today: date, n: int) -> list[tuple[int, int]]:
    year, month = today.year, today.month
    months = []
    for _ in range(n):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


def activity_timeline(db: Session, user_id: uuid.UUID, today: date) -> list[dict]:
    completed = [
        lab for lab in _user_labs(db, user_id) if lab.status == "Completed" and lab.date_completed is not None
    ]
    counts = Counter((lab.date_completed.year, lab.date_completed.month) for lab in completed)
    # Months with no completed labs appear as real zeroes so the axis is continuous.
    return [
        {"label": f"{year:04d}-{month:02d}", "count": counts.get((year, month), 0)}
        for year, month in _last_n_months(today, TIMELINE_MONTHS)
    ]


def skills_practiced(db: Session, user_id: uuid.UUID) -> list[dict]:
    practiced = [lab for lab in _user_labs(db, user_id) if is_practiced(lab)]
    return _to_points(Counter(skill.name for lab in practiced for skill in lab.skills), TOP_N)


def tools_used(db: Session, user_id: uuid.UUID) -> list[dict]:
    practiced = [lab for lab in _user_labs(db, user_id) if is_practiced(lab)]
    return _to_points(Counter(tool.name for lab in practiced for tool in lab.tools), TOP_N)


def mitre_coverage_by_tactic(db: Session, user_id: uuid.UUID) -> list[dict]:
    """Number of distinct practiced techniques per tactic."""
    practiced = [lab for lab in _user_labs(db, user_id) if is_practiced(lab)]
    seen: dict[str, set[uuid.UUID]] = {}
    for lab in practiced:
        for mapping in lab.techniques:
            seen.setdefault(mapping.technique.tactic, set()).add(mapping.technique.id)
    return _to_points(Counter({tactic: len(ids) for tactic, ids in seen.items()}))


# ---- recent activity ------------------------------------------------------------


def get_recent_activity(db: Session, user_id: uuid.UUID) -> dict:
    labs = sorted(_user_labs(db, user_id), key=lambda lab: lab.updated_at, reverse=True)[:RECENT_LIMIT]

    challenges = sorted(_user_challenges(db, user_id), key=lambda c: c.created_at, reverse=True)[:RECENT_LIMIT]
    recent_challenges = [
        {
            "id": c.id,
            "ctf_event_id": c.ctf_event_id,
            "title": c.title,
            "category": c.category,
            "status": c.status,
            "event_name": c.event.name,
            "created_at": c.created_at,
        }
        for c in challenges
    ]

    practiced_skills = [s for s in list_skills_with_stats(db, user_id) if s["lab_count"] > 0]
    practiced_skills.sort(key=lambda s: s["last_practiced"], reverse=True)
    recent_skills = [
        {"id": s["id"], "name": s["name"], "last_practiced": s["last_practiced"]}
        for s in practiced_skills[:RECENT_LIMIT]
    ]

    return {
        "recent_labs": labs,
        "recent_ctf_challenges": recent_challenges,
        "recently_practiced_skills": recent_skills,
    }
