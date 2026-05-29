from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.common import TimestampMixin


class PrintRecord(TimestampMixin, Base):
    """Master: one record per print job."""
    __tablename__ = "print_records"

    printer_id = Column(Integer, ForeignKey("printer_configs.id"), nullable=True)
    printer_name = Column(String(64), default="")
    print_job_id = Column(String(64), index=True)
    filename = Column(String(256), default="")
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    status = Column(String(16), default="running")  # running / finished / failed

    printer = relationship("PrinterConfig", backref="print_records")
    details = relationship("PrintRecordDetail", back_populates="print_record",
                           cascade="all, delete-orphan", order_by="PrintRecordDetail.tray")


class PrintRecordDetail(TimestampMixin, Base):
    """Detail: per-tray filament usage within a print job."""
    __tablename__ = "print_record_details"

    print_record_id = Column(Integer, ForeignKey("print_records.id"), nullable=False)
    tray = Column(Integer, default=0)          # AMS tray (1-4) or 0 = EXT
    spool_id = Column(Integer, ForeignKey("spools.id"), nullable=True)
    filament_used_mm = Column(Float, default=0)
    filament_used_weight = Column(Float, default=0)
    filament_diameter = Column(Float, default=1.75)
    deducted = Column(Boolean, default=False)  # whether weight was deducted from spool
    remaining_percent_before = Column(Float, nullable=True)
    remaining_percent_after = Column(Float, nullable=True)

    print_record = relationship("PrintRecord", back_populates="details")
    spool = relationship("Spool", backref="print_record_details")
