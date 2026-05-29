from sqlalchemy import Boolean, Column, Integer, String
from app.database import Base
from app.models.common import TimestampMixin


class PrinterConfig(TimestampMixin, Base):
    __tablename__ = "printer_configs"

    name = Column(String(64), nullable=False)
    serial = Column(String(64), unique=True, nullable=False, index=True)
    ip_address = Column(String(64), nullable=False)
    access_code = Column(String(64), nullable=False)
    port = Column(Integer, default=8883)
    is_active = Column(Boolean, default=True)
