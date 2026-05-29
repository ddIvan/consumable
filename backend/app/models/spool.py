from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.common import TimestampMixin


class Spool(TimestampMixin, Base):
    __tablename__ = "spools"

    filament_id = Column(Integer, ForeignKey("filaments.id"), nullable=False)
    name = Column(String(128), nullable=False)
    label = Column(String(64), default="")  # user-printed label
    initial_weight = Column(Float, nullable=False)  # grams
    current_weight = Column(Float, nullable=False)  # grams
    is_active = Column(Boolean, default=True)
    ams_tray = Column(Integer, default=0)  # 0 = not in AMS, 1-4 = AMS slot
    activated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    filament = relationship("Filament", backref="spools")
