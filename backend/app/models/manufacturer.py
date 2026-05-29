from sqlalchemy import Column, String, Text
from app.database import Base
from app.models.common import TimestampMixin


class Manufacturer(TimestampMixin, Base):
    __tablename__ = "manufacturers"

    name = Column(String(128), unique=True, nullable=False, index=True)
    short_name = Column(String(32), default="")
    description = Column(Text, default="")
    website = Column(String(256), default="")
