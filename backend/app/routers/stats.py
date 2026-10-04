from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.stats import ChartPoint, OverviewOut, RecentActivityOut
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=OverviewOut)
def overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.get_overview(db, current_user.id, date.today())


@router.get("/labs-by-category", response_model=list[ChartPoint])
def labs_by_category(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.labs_by_category(db, current_user.id)


@router.get("/difficulty-distribution", response_model=list[ChartPoint])
def difficulty_distribution(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.difficulty_distribution(db, current_user.id)


@router.get("/activity-timeline", response_model=list[ChartPoint])
def activity_timeline(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.activity_timeline(db, current_user.id, date.today())


@router.get("/skills-practiced", response_model=list[ChartPoint])
def skills_practiced(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.skills_practiced(db, current_user.id)


@router.get("/tools-used", response_model=list[ChartPoint])
def tools_used(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.tools_used(db, current_user.id)


@router.get("/mitre-coverage", response_model=list[ChartPoint])
def mitre_coverage(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.mitre_coverage_by_tactic(db, current_user.id)


@router.get("/recent", response_model=RecentActivityOut)
def recent_activity(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return stats_service.get_recent_activity(db, current_user.id)
