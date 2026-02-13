from sqlalchemy import Column, Integer, String, Text
from app.db.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=True)
    type = Column(String, default="string") # string, number, boolean, json
    description = Column(String, nullable=True)
    group = Column(String, default="general") # general, hardware, payment
