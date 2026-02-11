from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    slot_code = Column(String)  # A1, A2, B1...
    product_id = Column(Integer, ForeignKey("products.id"))
    stock = Column(Integer, default=0)
    capacity = Column(Integer, default=10)
    
    # Relationships
    machine = relationship("Machine", back_populates="slots")
    product = relationship("Product", back_populates="slots")
