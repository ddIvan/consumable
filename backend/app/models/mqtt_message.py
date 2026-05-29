from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.database import Base
from app.models.common import TimestampMixin


class MqttMessage(TimestampMixin, Base):
    __tablename__ = "mqtt_messages"

    printer_id = Column(Integer, nullable=True)
    printer_name = Column(String(64), default="")
    topic = Column(String(256), default="")
    payload = Column(Text, default="")
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
