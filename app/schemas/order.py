from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class OrderCreate(BaseModel):
    machine_id: int
    slot_no: str
    quantity: int = 1
    payment_method: str = 'cash'  # cash, qr_code, card

class OrderOut(BaseModel):
    id: int
    machine_id: int
    slot_no: str
    quantity: int
    status: str
    total_price: float
    payment_method: str
    created_at: datetime
    
    class Config:
        from_attributes = True