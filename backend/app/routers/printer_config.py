from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.printer import PrinterConfig
from app.schemas import PrinterCreate, PrinterOut, PrinterUpdate

router = APIRouter(prefix="/api/printers", tags=["printers"])


@router.get("", response_model=list[PrinterOut])
def list_printers(db: Session = Depends(get_db)):
    return db.query(PrinterConfig).order_by(PrinterConfig.name).all()


@router.post("", response_model=PrinterOut, status_code=status.HTTP_201_CREATED)
def create_printer(data: PrinterCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(PrinterConfig)
        .filter(PrinterConfig.serial == data.serial)
        .first()
    )
    if existing:
        raise HTTPException(400, "Printer with this serial already exists")
    p = PrinterConfig(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{printer_id}", response_model=PrinterOut)
def get_printer(printer_id: int, db: Session = Depends(get_db)):
    p = db.query(PrinterConfig).filter(PrinterConfig.id == printer_id).first()
    if not p:
        raise HTTPException(404)
    return p


@router.put("/{printer_id}", response_model=PrinterOut)
def update_printer(
    printer_id: int, data: PrinterUpdate, db: Session = Depends(get_db)
):
    p = db.query(PrinterConfig).filter(PrinterConfig.id == printer_id).first()
    if not p:
        raise HTTPException(404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    p = db.query(PrinterConfig).filter(PrinterConfig.id == printer_id).first()
    if not p:
        raise HTTPException(404)
    db.delete(p)
    db.commit()
