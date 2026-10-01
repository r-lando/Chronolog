import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.learning_goal import LearningGoal
from app.models.skill import Skill
from app.models.user import User
from app.schemas.learning_goal import (
    LearningGoalCreate,
    LearningGoalOut,
    LearningGoalProgressOut,
    LearningGoalUpdate,
)
from app.services.roadmap_service import get_goal_progress, get_owned_goal_or_404, list_goals_for_user, validate_no_cycle

router = APIRouter(prefix="/learning-goals", tags=["roadmap"])


def _validate_related_skill(db: Session, skill_id: uuid.UUID | None) -> None:
    if skill_id is not None and db.get(Skill, skill_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="related_skill_id does not exist.")


def _validate_parent(db: Session, user_id: uuid.UUID, parent_id: uuid.UUID | None) -> None:
    if parent_id is not None:
        get_owned_goal_or_404(db, parent_id, user_id)  # 404s if it doesn't exist or isn't theirs


@router.get("", response_model=list[LearningGoalOut])
def list_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_goals_for_user(db, current_user.id)


@router.post("", response_model=LearningGoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: LearningGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_parent(db, current_user.id, payload.parent_goal_id)
    _validate_related_skill(db, payload.related_skill_id)

    goal = LearningGoal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.put("/{goal_id}", response_model=LearningGoalOut)
def update_goal(
    goal_id: uuid.UUID,
    payload: LearningGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = get_owned_goal_or_404(db, goal_id, current_user.id)
    _validate_parent(db, current_user.id, payload.parent_goal_id)
    _validate_related_skill(db, payload.related_skill_id)
    validate_no_cycle(db, goal.id, payload.parent_goal_id)

    for field, value in payload.model_dump().items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    goal = get_owned_goal_or_404(db, goal_id, current_user.id)
    db.delete(goal)  # cascades to children (ORM + DB-level FK cascade)
    db.commit()


@router.get("/{goal_id}/progress", response_model=LearningGoalProgressOut)
def goal_progress(
    goal_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    goal = get_owned_goal_or_404(db, goal_id, current_user.id)
    return get_goal_progress(db, goal, current_user.id)
