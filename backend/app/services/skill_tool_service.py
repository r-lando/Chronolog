"""
Skill and tool statistics.

Skills and tools are shared master-list rows (not owned by a specific
user), but every derived statistic here — lab count, last practiced,
related labs/tools — is scoped to labs owned by the requesting user.
This keeps a single-user deployment fully correct today and makes the
scoping already in place if TALA ever supports more than one account.

Deliberately implemented with straightforward Python loops over a
small, user-owned dataset rather than dense aggregate SQL: a personal
lab journal will have dozens-to-low-hundreds of labs, not millions of
rows, so readability wins here over query optimization.
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.lab import Lab
from app.models.skill import Skill
from app.models.tool import Tool


def _most_recent_activity_date(lab: Lab) -> date:
    """The most meaningful "when was this practiced" date available for a lab."""
    if lab.date_completed:
        return lab.date_completed
    if lab.date_started:
        return lab.date_started
    return lab.created_at.date()


def get_or_create_skill(db: Session, name: str) -> Skill:
    normalized = name.strip()
    skill = db.query(Skill).filter(Skill.name.ilike(normalized)).first()
    if skill is None:
        skill = Skill(name=normalized)
        db.add(skill)
        db.flush()
    return skill


def get_or_create_tool(db: Session, name: str) -> Tool:
    normalized = name.strip()
    tool = db.query(Tool).filter(Tool.name.ilike(normalized)).first()
    if tool is None:
        tool = Tool(name=normalized)
        db.add(tool)
        db.flush()
    return tool


def list_skills_with_stats(db: Session, user_id: uuid.UUID) -> list[dict]:
    skills = db.query(Skill).order_by(Skill.name).all()
    results = []
    for skill in skills:
        user_labs = [lab for lab in skill.labs if lab.user_id == user_id]
        last_practiced = max((_most_recent_activity_date(lab) for lab in user_labs), default=None)
        results.append(
            {
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "description": skill.description,
                "lab_count": len(user_labs),
                "last_practiced": last_practiced,
            }
        )
    return results


def get_skill_detail(db: Session, skill_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
    skill = db.get(Skill, skill_id)
    if skill is None:
        return None

    user_labs = [lab for lab in skill.labs if lab.user_id == user_id]
    last_practiced = max((_most_recent_activity_date(lab) for lab in user_labs), default=None)

    related_tool_map = {}
    related_technique_map = {}
    for lab in user_labs:
        for tool in lab.tools:
            related_tool_map[tool.id] = tool
        for lab_technique in lab.techniques:
            related_technique_map[lab_technique.technique.id] = lab_technique.technique

    return {
        "id": skill.id,
        "name": skill.name,
        "category": skill.category,
        "description": skill.description,
        "lab_count": len(user_labs),
        "last_practiced": last_practiced,
        "related_labs": sorted(user_labs, key=_most_recent_activity_date, reverse=True),
        "related_tools": list(related_tool_map.values()),
        "related_techniques": list(related_technique_map.values()),
    }


def list_tools_with_stats(db: Session, user_id: uuid.UUID) -> list[dict]:
    tools = db.query(Tool).order_by(Tool.name).all()
    results = []
    for tool in tools:
        user_labs = [lab for lab in tool.labs if lab.user_id == user_id]
        last_used = max((_most_recent_activity_date(lab) for lab in user_labs), default=None)
        results.append(
            {
                "id": tool.id,
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "lab_count": len(user_labs),
                "last_used": last_used,
            }
        )
    return results


def get_tool_detail(db: Session, tool_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
    tool = db.get(Tool, tool_id)
    if tool is None:
        return None

    user_labs = [lab for lab in tool.labs if lab.user_id == user_id]
    last_used = max((_most_recent_activity_date(lab) for lab in user_labs), default=None)

    related_skill_map = {}
    related_technique_map = {}
    for lab in user_labs:
        for skill in lab.skills:
            related_skill_map[skill.id] = skill
        for lab_technique in lab.techniques:
            related_technique_map[lab_technique.technique.id] = lab_technique.technique

    return {
        "id": tool.id,
        "name": tool.name,
        "category": tool.category,
        "description": tool.description,
        "lab_count": len(user_labs),
        "last_used": last_used,
        "related_labs": sorted(user_labs, key=_most_recent_activity_date, reverse=True),
        "related_skills": list(related_skill_map.values()),
        "related_techniques": list(related_technique_map.values()),
    }
