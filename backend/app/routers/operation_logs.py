from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.operation_log import OperationLog
from app.schemas import OperationLogOut

router = APIRouter(prefix="/api/operation-logs", tags=["operation-logs"])


@router.get("", response_model=list[OperationLogOut])
def list_logs(
    search: str = "",
    level: str = "",
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(OperationLog)
    if search:
        q = q.filter(
            or_(
                OperationLog.message.ilike(f"%{search}%"),
                OperationLog.action.ilike(f"%{search}%"),
                OperationLog.target.ilike(f"%{search}%"),
            )
        )
    if level:
        q = q.filter(OperationLog.level == level)
    return q.order_by(OperationLog.created_at.desc()).offset(offset).limit(limit).all()


@router.delete("", status_code=204)
def clear_logs(db: Session = Depends(get_db)):
    db.query(OperationLog).delete()
    db.commit()
