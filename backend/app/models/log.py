from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class RefillLog(Base):
    __tablename__ = "refill_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))
    slot_id = Column(Integer, ForeignKey("slots.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False) # Số lượng nạp thêm
    old_quantity = Column(Integer, nullable=False) # Số lượng trước khi nạp
    new_quantity = Column(Integer, nullable=False) # Số lượng sau khi nạp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    machine = relationship("Machine")
    slot = relationship("Slot")
    product = relationship("Product")
