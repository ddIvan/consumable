from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.common import TimestampMixin


class Filament(TimestampMixin, Base):
    __tablename__ = "filaments"

    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    name = Column(String(128), nullable=False)
    filament_type = Column(String(32), nullable=False)  # PLA, PETG, ABS, TPU, PA, PC, etc.
    color = Column(String(7), default="#FFFFFF")  # hex
    color_name = Column(String(64), default="")
    diameter = Column(Float, default=1.75)
    density = Column(Float, nullable=False)  # g/cm³

    manufacturer = relationship("Manufacturer", backref="filaments")
