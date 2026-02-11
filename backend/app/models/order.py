from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as EnumType
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    DISPENSING = "DISPENSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(Integer, unique=True, index=True) # PayOS strict integer
    product_id = Column(Integer, ForeignKey("products.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    amount = Column(Integer)
    status = Column(String, default=OrderStatus.PENDING)
    
    payment_url = Column(String, nullable=True)
    qr_code = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product")
    machine = relationship("Machine", back_populates="orders")
