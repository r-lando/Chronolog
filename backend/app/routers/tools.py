import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.tool import ToolDetailOut, ToolWithStatsOut
from app.services.skill_tool_service import get_tool_detail, list_tools_with_stats

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolWithStatsOut])
def list_tools(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_tools_with_stats(db, current_user.id)


@router.get("/{tool_id}", response_model=ToolDetailOut)
def get_tool(tool_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    detail = get_tool_detail(db, tool_id, current_user.id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return detail
