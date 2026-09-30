"""
Shared activity rules.

One definition of "practiced" used by every statistic in the app
(dashboard, Skills, Tools, MITRE pages). Before this module existed,
the Skills/Tools/MITRE pages counted any lab with a skill attached —
including labs still marked "Planned", which the user hasn't actually
done yet. That would inflate hands-on experience numbers, which is the
opposite of what a credible learning journal should show.

Rule: a lab counts as practiced activity unless its status is "Planned".
(In Progress, Completed, Paused, and Archived labs all represent real
hands-on time.)
"""

from datetime import date

from app.models.lab import Lab

NOT_YET_PRACTICED_STATUSES = {"Planned"}


def is_practiced(lab: Lab) -> bool:
    return lab.status not in NOT_YET_PRACTICED_STATUSES


def most_recent_activity_date(lab: Lab) -> date:
    """The most meaningful "when was this practiced" date available for a lab."""
    if lab.date_completed:
        return lab.date_completed
    if lab.date_started:
        return lab.date_started
    return lab.created_at.date()
