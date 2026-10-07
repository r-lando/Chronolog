"""
Global search across labs, CTFs, skills, tools, MITRE techniques, tags,
and findings (spec section 13).

Scoping rule: labs, CTF challenges, findings, and tags are searched only
within the current user's own data (joined through ownership the same
way every other router in this app enforces it). Skills, tools, and
MITRE techniques are shared reference lists — like the Skills and Tools
pages themselves, searching them returns matches regardless of whether
the current user has used them yet, so a result like "SIEM" can lead
someone to attach it to a lab even on their very first search.

Each entity type is capped at RESULTS_PER_TYPE matches so one broad
term (e.g. "the") can't return an unbounded flood from any single
source — this is a basic safeguard against both a confusing UI and an
expensive query, not a full pagination system.
"""

import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.ctf import CtfChallenge, CtfEvent
from app.models.finding import Finding
from app.models.lab import Lab
from app.models.mitre import MitreTechnique
from app.models.skill import Skill
from app.models.tag import Tag
from app.models.tool import Tool

RESULTS_PER_TYPE = 8


def global_search(db: Session, user_id: uuid.UUID, query: str) -> list[dict]:
    like = f"%{query}%"
    results: list[dict] = []

    labs = (
        db.query(Lab)
        .filter(Lab.user_id == user_id, or_(Lab.title.ilike(like), Lab.description.ilike(like)))
        .limit(RESULTS_PER_TYPE)
        .all()
    )
    results += [
        {"id": str(lab.id), "type": "lab", "title": lab.title, "subtitle": lab.category, "url": f"/labs/{lab.id}"}
        for lab in labs
    ]

    challenges = (
        db.query(CtfChallenge, CtfEvent.name)
        .join(CtfEvent, CtfChallenge.ctf_event_id == CtfEvent.id)
        .filter(CtfEvent.user_id == user_id, CtfChallenge.title.ilike(like))
        .limit(RESULTS_PER_TYPE)
        .all()
    )
    results += [
        {
            "id": str(challenge.id),
            "type": "ctf_challenge",
            "title": challenge.title,
            "subtitle": event_name,
            "url": f"/ctfs/challenges/{challenge.id}",
        }
        for challenge, event_name in challenges
    ]

    findings = (
        db.query(Finding, Lab.title)
        .join(Lab, Finding.lab_id == Lab.id)
        .filter(Lab.user_id == user_id, Finding.title.ilike(like))
        .limit(RESULTS_PER_TYPE)
        .all()
    )
    results += [
        {
            "id": str(finding.id),
            "type": "finding",
            "title": finding.title,
            "subtitle": f"Finding in {lab_title}",
            "url": f"/labs/{finding.lab_id}",
        }
        for finding, lab_title in findings
    ]

    tags = (
        db.query(Tag)
        .join(Tag.labs)  # restrict to tags actually used on one of this user's labs
        .filter(Lab.user_id == user_id, Tag.name.ilike(like))
        .distinct()
        .limit(RESULTS_PER_TYPE)
        .all()
    )
    results += [
        {"id": str(tag.id), "type": "tag", "title": tag.name, "subtitle": "Tag", "url": f"/labs?tag={tag.name}"}
        for tag in tags
    ]

    skills = db.query(Skill).filter(Skill.name.ilike(like)).limit(RESULTS_PER_TYPE).all()
    results += [
        {"id": str(skill.id), "type": "skill", "title": skill.name, "subtitle": "Skill", "url": f"/skills/{skill.id}"}
        for skill in skills
    ]

    tools = db.query(Tool).filter(Tool.name.ilike(like)).limit(RESULTS_PER_TYPE).all()
    results += [
        {"id": str(tool.id), "type": "tool", "title": tool.name, "subtitle": "Tool", "url": f"/tools/{tool.id}"}
        for tool in tools
    ]

    techniques = (
        db.query(MitreTechnique)
        .filter(or_(MitreTechnique.name.ilike(like), MitreTechnique.technique_id.ilike(like)))
        .limit(RESULTS_PER_TYPE)
        .all()
    )
    results += [
        {
            "id": str(technique.id),
            "type": "mitre_technique",
            "title": f"{technique.technique_id} — {technique.name}",
            "subtitle": technique.tactic,
            "url": f"/mitre/{technique.id}",
        }
        for technique in techniques
    ]

    return results
