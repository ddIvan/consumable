from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.print_record import PrintRecord, PrintRecordDetail
from app.models.spool import Spool
from app.schemas import PrintRecordDetailOut, PrintRecordOut
from app.services.filament_calc import filament_weight, get_filament_params

router = APIRouter(prefix="/api/print-records", tags=["print-records"])


@router.get("", response_model=list[PrintRecordOut])
def list_print_records(
    limit: int = Query(100, le=500),
    offset: int = 0,
    print_job_id: str = "",
    db: Session = Depends(get_db),
):
    q = db.query(PrintRecord).options(joinedload(PrintRecord.details))
    if print_job_id:
        q = q.filter(PrintRecord.print_job_id == print_job_id)
    records = q.order_by(PrintRecord.created_at.desc()).offset(offset).limit(limit).all()

    # attach spool_name to each detail
    for r in records:
        for d in r.details:
            d.spool_name = d.spool.name if d.spool else ""
    return records


@router.post("/details/{detail_id}/deduct", response_model=PrintRecordDetailOut)
def deduct_print_detail(detail_id: int, db: Session = Depends(get_db)):
    """Manually deduct the filament used in this detail row from its spool."""
    d = db.query(PrintRecordDetail).filter(PrintRecordDetail.id == detail_id).first()
    if not d:
        raise HTTPException(404)
    if d.deducted:
        raise HTTPException(400, "已扣减过，不能重复操作")
    if not d.spool_id:
        raise HTTPException(400, "该记录没有关联料盘，无法扣减")

    spool = db.query(Spool).filter(Spool.id == d.spool_id).first()
    if not spool:
        raise HTTPException(400, "关联料盘不存在")

    _, density = get_filament_params(db, d.spool_id)
    weight = filament_weight(d.filament_used_mm, d.filament_diameter, density)

    spool.current_weight = max(0, round(spool.current_weight - weight, 2))
    d.deducted = True
    db.commit()
    db.refresh(d)

    d.spool_name = spool.name
    return d
