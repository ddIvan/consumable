from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.filament import Filament
from app.models.spool import Spool
from app.schemas import SpoolCreate, SpoolOut, SpoolUpdate
from app.schemas import _resolve_location

router = APIRouter(prefix="/api/spools", tags=["spools"])


@router.get("", response_model=list[SpoolOut])
def list_spools(db: Session = Depends(get_db)):
    q = (
        db.query(Spool)
        .options(joinedload(Spool.filament).joinedload(Filament.manufacturer))
        .order_by(Spool.is_active.desc(), Spool.name)
        .all()
    )
    return [_enrich(s) for s in q]


@router.post("", response_model=SpoolOut, status_code=status.HTTP_201_CREATED)
def create_spool(data: SpoolCreate, db: Session = Depends(get_db)):
    s = Spool(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return _enrich(s)


@router.get("/{spool_id}", response_model=SpoolOut)
def get_spool(spool_id: int, db: Session = Depends(get_db)):
    s = (
        db.query(Spool)
        .options(joinedload(Spool.filament).joinedload(Filament.manufacturer))
        .filter(Spool.id == spool_id)
        .first()
    )
    if not s:
        raise HTTPException(404)
    return _enrich(s)


@router.put("/{spool_id}", response_model=SpoolOut)
def update_spool(spool_id: int, data: SpoolUpdate, db: Session = Depends(get_db)):
    s = db.query(Spool).filter(Spool.id == spool_id).first()
    if not s:
        raise HTTPException(404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return _enrich(s)


@router.delete("/{spool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spool(spool_id: int, db: Session = Depends(get_db)):
    s = db.query(Spool).filter(Spool.id == spool_id).first()
    if not s:
        raise HTTPException(404)
    db.delete(s)
    db.commit()


def _enrich(s: Spool) -> dict:
    d = s.__dict__.copy()
    fil = s.filament
    d["filament_name"] = fil.name if fil else ""
    d["filament_type"] = fil.filament_type if fil else ""
    d["filament_color"] = fil.color if fil else ""
    d["manufacturer_name"] = fil.manufacturer.name if fil and fil.manufacturer else ""
    d["location"] = _resolve_location(s.is_active, s.ams_tray)
    return d
