"""
Learning roadmap logic.

Two things worth calling out:

1. Cycle prevention: a self-referencing tree can be pointed at itself,
   creating an infinite loop that would hang any code walking the tree
   (rendering it, deleting it, computing rollups). validate_no_cycle()
   walks from the proposed parent up to the root and rejects the change
   if it ever reaches the goal being edited.

2. Recommendations are simple, explainable rules over real data — not a
   model, not a guess. "0 labs -> do one", "1-2 -> keep going", "3+ ->
   try something harder" is the entire algorithm. This matches the
   product's stance of not fabricating measures of skill.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ctf import CtfChallenge, CtfEvent
from app.models.learning_goal import LearningGoal
from app.services.activity import is_practiced


def get_owned_goal_or_404(db: Session, goal_id: uuid.UUID, user_id: uuid.UUID) -> LearningGoal:
    goal = db.get(LearningGoal, goal_id)
    if goal is None or goal.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning goal not found")
    return goal


def list_goals_for_user(db: Session, user_id: uuid.UUID) -> list[LearningGoal]:
    return db.query(LearningGoal).filter(LearningGoal.user_id == user_id).order_by(LearningGoal.created_at).all()


def validate_no_cycle(db: Session, goal_id: uuid.UUID | None, proposed_parent_id: uuid.UUID | None) -> None:
    """
    Raises 400 if proposed_parent_id is the goal itself or one of its
    own descendants (which would make it its own ancestor once attached).
    goal_id is None when creating a brand-new goal — nothing to check.
    """
    if proposed_parent_id is None or goal_id is None:
        return
    if proposed_parent_id == goal_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A goal cannot be its own parent.")

    cursor = db.get(LearningGoal, proposed_parent_id)
    visited = set()
    while cursor is not None:
        if cursor.id == goal_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That would make this goal a parent of itself (a cycle).",
            )
        if cursor.id in visited:
            break  # defensive: an existing cycle somehow already present — stop rather than loop forever
        visited.add(cursor.id)
        cursor = cursor.parent


def _recommend_next_activity(skill_name: str, lab_count: int) -> str:
    if lab_count == 0:
        return f"Document your first lab practicing {skill_name} to start building this goal's progress."
    if lab_count < 3:
        return f"You've practiced {skill_name} in {lab_count} lab(s) — a couple more will solidify it."
    return f"Solid practice in {skill_name} ({lab_count} labs). Try a harder-difficulty lab next."


def get_goal_progress(db: Session, goal: LearningGoal, user_id: uuid.UUID) -> dict:
    if goal.related_skill_id is not None and goal.related_skill is not None:
        skill = goal.related_skill
        user_labs = [lab for lab in skill.labs if lab.user_id == user_id and is_practiced(lab)]

        related_challenges = (
            db.query(CtfChallenge)
            .join(CtfEvent, CtfChallenge.ctf_event_id == CtfEvent.id)
            .filter(CtfEvent.user_id == user_id, CtfChallenge.skills.any(id=skill.id))
            .all()
        )

        return {
            "goal_id": goal.id,
            "has_related_skill": True,
            "labs_completed": len(user_labs),
            "related_labs": user_labs,
            "related_ctf_challenges": related_challenges,
            "recommended_next_activity": _recommend_next_activity(skill.name, len(user_labs)),
        }

    # Grouping node (e.g. "SOC Analyst"): roll up children instead.
    children = goal.children
    children_with_activity = 0
    for child in children:
        if child.related_skill_id and child.related_skill is not None:
            if any(lab.user_id == user_id and is_practiced(lab) for lab in child.related_skill.labs):
                children_with_activity += 1

    if not children:
        recommendation = "Add a sub-goal linked to a specific skill to start tracking progress here."
    elif children_with_activity == 0:
        recommendation = f"Start with any of the {len(children)} sub-goals under {goal.title}."
    elif children_with_activity < len(children):
        recommendation = f"{len(children) - children_with_activity} of {len(children)} sub-goals still need a first lab."
    else:
        recommendation = f"All sub-goals under {goal.title} have documented activity — consider a new goal."

    return {
        "goal_id": goal.id,
        "has_related_skill": False,
        "labs_completed": 0,
        "related_labs": [],
        "related_ctf_challenges": [],
        "recommended_next_activity": recommendation,
        "child_count": len(children),
        "children_with_activity": children_with_activity,
    }
