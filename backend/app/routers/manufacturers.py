from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manufacturer import Manufacturer
from app.schemas import (
    ManufacturerCreate,
    ManufacturerOut,
    ManufacturerUpdate,
)

router = APIRouter(prefix="/api/manufacturers", tags=["manufacturers"])


@router.get("", response_model=list[ManufacturerOut])
def list_manufacturers(db: Session = Depends(get_db)):
    return db.query(Manufacturer).order_by(Manufacturer.name).all()


@router.post("", response_model=ManufacturerOut, status_code=status.HTTP_201_CREATED)
def create_manufacturer(data: ManufacturerCreate, db: Session = Depends(get_db)):
    existing = db.query(Manufacturer).filter(Manufacturer.name == data.name).first()
    if existing:
        raise HTTPException(400, "Manufacturer already exists")
    m = Manufacturer(**data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/{manufacturer_id}", response_model=ManufacturerOut)
def get_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    m = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not m:
        raise HTTPException(404)
    return m


@router.put("/{manufacturer_id}", response_model=ManufacturerOut)
def update_manufacturer(
    manufacturer_id: int, data: ManufacturerUpdate, db: Session = Depends(get_db)
):
    m = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not m:
        raise HTTPException(404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{manufacturer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    m = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not m:
        raise HTTPException(404)
    db.delete(m)
    db.commit()
