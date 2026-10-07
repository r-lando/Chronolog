from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.search import SearchResponse
from app.services.search_service import global_search

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = global_search(db, current_user.id, q)
    return SearchResponse(query=q, results=results)
