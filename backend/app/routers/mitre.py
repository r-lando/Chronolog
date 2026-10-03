import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.mitre import MitreTechniqueDetailOut, MitreTechniqueWithStatsOut
from app.services.mitre_service import get_technique_detail, list_techniques_with_stats

router = APIRouter(prefix="/mitre-techniques", tags=["mitre"])


@router.get("", response_model=list[MitreTechniqueWithStatsOut])
def list_techniques(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_techniques_with_stats(db, current_user.id)


@router.get("/{technique_id}", response_model=MitreTechniqueDetailOut)
def get_technique(
    technique_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    detail = get_technique_detail(db, technique_id, current_user.id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technique not found")
    return detail
