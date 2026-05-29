from __future__ import annotations

import logging
import math
from typing import Optional

from sqlalchemy.orm import Session

from app.models.filament import Filament
from app.models.print_record import PrintRecord, PrintRecordDetail
from app.models.spool import Spool

logger = logging.getLogger(__name__)


def cross_section_area(diameter_mm: float) -> float:
    """mm²"""
    r = diameter_mm / 2
    return math.pi * r * r


def filament_weight(length_mm: float, diameter_mm: float, density_g_per_cm3: float) -> float:
    """Calculate filament weight in grams from length.

    weight(g) = length(mm) × area(mm²) × density(g/cm³) / 1000
    """
    area = cross_section_area(diameter_mm)
    volume_mm3 = length_mm * area  # mm³
    volume_cm3 = volume_mm3 / 1000  # 1 cm³ = 1000 mm³
    return volume_cm3 * density_g_per_cm3


def length_from_weight(weight_g: float, diameter_mm: float, density_g_per_cm3: float) -> float:
    """Reverse: calculate length in mm from weight."""
    area = cross_section_area(diameter_mm)
    return weight_g / (density_g_per_cm3 * area / 1000)


def record_consumption(
    db: Session,
    spool_id: Optional[int],
    printer_id: Optional[int],
    print_job_id: str,
    filename: str,
    filament_used_mm: float,
    diameter: float,
    density: float,
    remaining_before: Optional[float] = None,
    remaining_after: Optional[float] = None,
    status: str = "finished",
) -> PrintRecord:
    """Record a completed print's filament consumption."""
    weight = filament_weight(filament_used_mm, diameter, density)

    master = PrintRecord(
        printer_id=printer_id,
        print_job_id=print_job_id,
        filename=filename,
        status=status,
    )
    db.add(master)
    db.flush()

    detail = PrintRecordDetail(
        print_record_id=master.id,
        tray=0,
        spool_id=spool_id,
        filament_used_mm=filament_used_mm,
        filament_used_weight=weight,
        filament_diameter=diameter,
        deducted=True,
        remaining_percent_before=remaining_before,
        remaining_percent_after=remaining_after,
    )
    db.add(detail)

    # update spool remaining weight
    if spool_id:
        spool = db.query(Spool).filter(Spool.id == spool_id).first()
        if spool:
            spool.current_weight = max(0, spool.current_weight - weight)
            logger.info(
                "Spool %s: -%.2fg → %.2fg remaining",
                spool.name,
                weight,
                spool.current_weight,
            )

    db.commit()
    db.refresh(master)
    return master


def get_filament_params(db: Session, spool_id: int) -> tuple[float, float]:
    """Get (diameter, density) for a spool, falling back to defaults."""
    spool = db.query(Spool).filter(Spool.id == spool_id).first()
    if not spool:
        return 1.75, 1.24  # generic PLA default
    filament = db.query(Filament).filter(Filament.id == spool.filament_id).first()
    if not filament:
        return 1.75, 1.24
    return filament.diameter, filament.density
