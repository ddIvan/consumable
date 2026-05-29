from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Manufacturer ──────────────────────────────────────────────
class ManufacturerBase(BaseModel):
    name: str = Field(..., max_length=128)
    short_name: str = Field(default="", max_length=32)
    description: str = ""
    website: str = Field(default="", max_length=256)


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None


class ManufacturerOut(ManufacturerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Filament ──────────────────────────────────────────────────
class FilamentBase(BaseModel):
    manufacturer_id: int
    name: str = Field(..., max_length=128)
    filament_type: str = Field(..., max_length=32)
    color: str = "#FFFFFF"
    color_name: str = ""
    diameter: float = 1.75
    density: float = Field(..., gt=0)


class FilamentCreate(FilamentBase):
    pass


class FilamentUpdate(BaseModel):
    manufacturer_id: Optional[int] = None
    name: Optional[str] = None
    filament_type: Optional[str] = None
    color: Optional[str] = None
    color_name: Optional[str] = None
    diameter: Optional[float] = None
    density: Optional[float] = None


class FilamentOut(FilamentBase):
    id: int
    manufacturer_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Spool ─────────────────────────────────────────────────────

def _resolve_location(is_active: bool, ams_tray: int) -> str:
    if ams_tray > 0:
        return "AMS"
    if is_active:
        return "EXT"
    return "仓库"


class SpoolBase(BaseModel):
    filament_id: int
    name: str = Field(..., max_length=128)
    label: str = ""
    initial_weight: float = Field(..., gt=0)
    current_weight: float = Field(..., gt=0)
    is_active: bool = True
    ams_tray: int = 0


class SpoolCreate(SpoolBase):
    pass


class SpoolUpdate(BaseModel):
    filament_id: Optional[int] = None
    name: Optional[str] = None
    label: Optional[str] = None
    initial_weight: Optional[float] = None
    current_weight: Optional[float] = None
    is_active: Optional[bool] = None
    ams_tray: Optional[int] = None


class SpoolOut(SpoolBase):
    id: int
    location: str = ""
    filament_name: str = ""
    filament_type: str = ""
    filament_color: str = ""
    manufacturer_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SpoolRemaining(BaseModel):
    """Lightweight response for dashboard."""
    id: int
    name: str
    current_weight: float
    initial_weight: float
    remaining_pct: float
    location: str = ""
    ams_tray: int = 0
    filament_type: str = ""
    filament_color: str = ""
    manufacturer_name: str = ""


# ─── MqttMessage ──────────────────────────────────────────────
class MqttMessageOut(BaseModel):
    id: int
    printer_id: Optional[int] = None
    printer_name: str = ""
    topic: str = ""
    payload: str = ""
    received_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Operation Log ────────────────────────────────────────────
class OperationLogOut(BaseModel):
    id: int
    action: str
    target: str = ""
    message: str = ""
    level: str = "info"
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Dashboard location groups ────────────────────────────────

class TrayInfo(BaseModel):
    tray: int
    spool_id: int
    name: str
    filament_type: str
    filament_color: str
    manufacturer_name: str
    initial_weight: float
    current_weight: float
    remaining_pct: float


class LocationGroup(BaseModel):
    label: str
    total_spools: int
    total_weight: float
    total_remaining: float
    remaining_pct: float
    spools: list[SpoolRemaining] = []
    ams_trays: list[TrayInfo] = []


class SpoolLocations(BaseModel):
    ams: LocationGroup
    ext: LocationGroup
    warehouse: LocationGroup


# ─── PrintRecord (master-detail) ──────────────────────────────
class PrintRecordDetailDeduct(BaseModel):
    """Response for a deduct action on a detail row."""
    id: int
    tray: int
    spool_id: Optional[int] = None
    spool_name: str = ""
    filament_used_mm: float
    filament_used_weight: float
    deducted: bool


class PrintRecordDetailOut(PrintRecordDetailDeduct):
    remaining_percent_before: Optional[float] = None
    remaining_percent_after: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PrintRecordBase(BaseModel):
    printer_id: Optional[int] = None
    printer_name: str = ""
    print_job_id: str
    filename: str = ""
    status: str = "running"


class PrintRecordOut(PrintRecordBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime
    details: list[PrintRecordDetailOut] = []

    model_config = {"from_attributes": True}


# ─── Printer ───────────────────────────────────────────────────
class PrinterCreate(BaseModel):
    name: str = Field(..., max_length=64)
    serial: str = Field(..., max_length=64)
    ip_address: str = Field(..., max_length=64)
    access_code: str = Field(..., max_length=64)
    port: int = 8883


class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    access_code: Optional[str] = None
    port: Optional[int] = None
    is_active: Optional[bool] = None


class PrinterOut(BaseModel):
    id: int
    name: str
    serial: str
    ip_address: str
    port: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Printer Status (real-time) ────────────────────────────────
class PrinterStatus(BaseModel):
    connected: bool = False
    gcode_state: str = "idle"  # idle / running / pause / finish / failed
    gcode_file: str = ""
    mc_percent: int = 0          # print progress
    nozzle_temp: float = 0
    nozzle_target: float = 0
    bed_temp: float = 0
    bed_target: float = 0
    filament_used_mm: float = 0
    mc_remaining_percent: float = 100
    current_tray: int = 0
    print_job_id: str = ""


# ─── Dashboard ─────────────────────────────────────────────────
class DashboardSummary(BaseModel):
    total_spools: int
    active_spools: int
    total_filaments: float  # total remaining weight
    recent_records: list[PrintRecordOut] = []
    spools: list[SpoolRemaining] = []
    printer_status: Optional[PrinterStatus] = None
