from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.filament import Filament
from app.schemas import FilamentCreate, FilamentOut, FilamentUpdate

router = APIRouter(prefix="/api/filaments", tags=["filaments"])


@router.get("", response_model=list[FilamentOut])
def list_filaments(db: Session = Depends(get_db)):
    q = (
        db.query(Filament)
        .options(joinedload(Filament.manufacturer))
        .order_by(Filament.name)
        .all()
    )
    result = []
    for f in q:
        d = f.__dict__.copy()
        d["manufacturer_name"] = f.manufacturer.name if f.manufacturer else ""
        result.append(d)
    return result


@router.post("", response_model=FilamentOut, status_code=status.HTTP_201_CREATED)
def create_filament(data: FilamentCreate, db: Session = Depends(get_db)):
    f = Filament(**data.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return _enrich(f)


@router.get("/{filament_id}", response_model=FilamentOut)
def get_filament(filament_id: int, db: Session = Depends(get_db)):
    f = (
        db.query(Filament)
        .options(joinedload(Filament.manufacturer))
        .filter(Filament.id == filament_id)
        .first()
    )
    if not f:
        raise HTTPException(404)
    return _enrich(f)


@router.put("/{filament_id}", response_model=FilamentOut)
def update_filament(
    filament_id: int, data: FilamentUpdate, db: Session = Depends(get_db)
):
    f = db.query(Filament).filter(Filament.id == filament_id).first()
    if not f:
        raise HTTPException(404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return _enrich(f)


@router.delete("/{filament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_filament(filament_id: int, db: Session = Depends(get_db)):
    f = db.query(Filament).filter(Filament.id == filament_id).first()
    if not f:
        raise HTTPException(404)
    db.delete(f)
    db.commit()


def _enrich(f: Filament) -> dict:
    """Attach manufacturer_name."""
    d = f.__dict__.copy()
    d["manufacturer_name"] = f.manufacturer.name if f.manufacturer else ""
    return d
