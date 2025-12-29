from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class OrderCreate(BaseModel):
    product_id: int
    price_snapshot: float
    slot_id: int
    status: str = 'pending'

class OrderOut(BaseModel):
    order_id: int
    product_id: int
    price_snapshot: float
    slot_id: int
    status: str
    create_at: datetime
    
    class Config:
        from_attributes = True