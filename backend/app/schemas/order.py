from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class OrderCreate(BaseModel):
    product_id: int
    price_snapshot: float
    slot_id: Optional[int] = None  # Optional for demo without slots
    status_payment: str = 'pending'
    status_slots: str = 'pending'

class OrderOut(BaseModel):
    order_id: int
    product_id: int
    price_snapshot: float
    slot_id: Optional[int] = None  # Optional for demo without slots
    status_payment: str
    status_slots: str
    created_at: datetime
    
    class Config:
        from_attributes = True