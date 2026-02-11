from sqlalchemy import Column, Integer, String, Boolean, Float, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Integer)
    image_url = Column(String)
    description = Column(Text, nullable=True)
    category = Column(String, default="drink")
    is_available = Column(Boolean, default=True)
    
    # Relationships
    slots = relationship("Slot", back_populates="product")