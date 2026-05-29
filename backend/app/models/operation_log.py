from sqlalchemy import Column, String
from app.database import Base
from app.models.common import TimestampMixin


class OperationLog(TimestampMixin, Base):
    __tablename__ = "operation_logs"

    action = Column(String(64), nullable=False)    # e.g. printer_connect, spool_update
    target = Column(String(128), default="")       # e.g. Printer name
    message = Column(String(512), default="")      # e.g. Connection failed: timeout
    level = Column(String(16), default="info")     # info / warning / error
