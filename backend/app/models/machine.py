from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    location = Column(String)
    status = Column(String, default="online")  # online, offline, error, maintenance
    secret_key = Column(String, unique=True) # Check against X-Machine-Key header
    last_ping = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    slots = relationship("Slot", back_populates="machine")
    orders = relationship("Order", back_populates="machine")
