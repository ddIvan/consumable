from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.print_record import PrintRecord, PrintRecordDetail
from app.models.spool import Spool
from app.schemas import (
    DashboardSummary,
    LocationGroup,
    PrintRecordOut,
    PrinterStatus,
    SpoolLocations,
    SpoolRemaining,
    TrayInfo,
    _resolve_location,
)
from app.services.mqtt_service import manager

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _build_remaining(s: Spool) -> SpoolRemaining:
    fil = s.filament
    remaining_pct = round(s.current_weight / s.initial_weight * 100, 1) if s.initial_weight > 0 else 0
    return SpoolRemaining(
        id=s.id,
        name=s.name,
        current_weight=s.current_weight,
        initial_weight=s.initial_weight,
        remaining_pct=remaining_pct,
        location=_resolve_location(s.is_active, s.ams_tray),
        ams_tray=s.ams_tray,
        filament_type=fil.filament_type if fil else "",
        filament_color=fil.color if fil else "",
        manufacturer_name=fil.manufacturer.name if fil and fil.manufacturer else "",
    )


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    spools = (
        db.query(Spool)
        .options(joinedload(Spool.filament))
        .order_by(Spool.current_weight.asc())
        .all()
    )
    total_filaments = sum(s.current_weight for s in spools)

    recent = (
        db.query(PrintRecord)
        .options(joinedload(PrintRecord.details).joinedload(PrintRecordDetail.spool))
        .order_by(PrintRecord.created_at.desc())
        .limit(10)
        .all()
    )

    spool_items = [_build_remaining(s) for s in spools]

    # printer status
    printer_status = None
    for pid, client in manager._printers.items():
        printer_status = client.status
        break

    return DashboardSummary(
        total_spools=len(spools),
        active_spools=sum(1 for s in spools if s.is_active),
        total_filaments=round(total_filaments, 1),
        recent_records=recent,
        spools=spool_items,
        printer_status=printer_status,
    )


@router.get("/locations", response_model=SpoolLocations)
def spool_locations(db: Session = Depends(get_db)):
    spools = (
        db.query(Spool)
        .options(joinedload(Spool.filament))
        .all()
    )

    ams_list: list[Spool] = []
    ext_list: list[Spool] = []
    warehouse_list: list[Spool] = []

    for s in spools:
        loc = _resolve_location(s.is_active, s.ams_tray)
        if loc == "AMS":
            ams_list.append(s)
        elif loc == "EXT":
            ext_list.append(s)
        else:
            warehouse_list.append(s)

    def make_group(spools_in_group: list[Spool]) -> LocationGroup:
        items = [_build_remaining(s) for s in spools_in_group]
        total_w = sum(s.initial_weight for s in spools_in_group)
        total_r = sum(s.current_weight for s in spools_in_group)
        return LocationGroup(
            label="",
            total_spools=len(spools_in_group),
            total_weight=round(total_w, 1),
            total_remaining=round(total_r, 1),
            remaining_pct=round(total_r / total_w * 100, 1) if total_w > 0 else 0,
            spools=items,
        )

    ams_trays = []
    for s in ams_list:
        remaining_pct = round(s.current_weight / s.initial_weight * 100, 1) if s.initial_weight > 0 else 0
        fil = s.filament
        ams_trays.append(TrayInfo(
            tray=s.ams_tray,
            spool_id=s.id,
            name=s.name,
            filament_type=fil.filament_type if fil else "",
            filament_color=fil.color if fil else "",
            manufacturer_name=fil.manufacturer.name if fil and fil.manufacturer else "",
            initial_weight=s.initial_weight,
            current_weight=s.current_weight,
            remaining_pct=remaining_pct,
        ))

    ams_group = make_group(ams_list)
    ams_group.ams_trays = sorted(ams_trays, key=lambda t: t.tray)

    return SpoolLocations(
        ams=ams_group,
        ext=make_group(ext_list),
        warehouse=make_group(warehouse_list),
    )
