import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.skill import SkillDetailOut, SkillWithStatsOut
from app.services.skill_tool_service import get_skill_detail, list_skills_with_stats

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillWithStatsOut])
def list_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_skills_with_stats(db, current_user.id)


@router.get("/{skill_id}", response_model=SkillDetailOut)
def get_skill(skill_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    detail = get_skill_detail(db, skill_id, current_user.id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return detail
