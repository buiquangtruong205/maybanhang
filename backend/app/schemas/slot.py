from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SlotCreate(BaseModel):
    machine_id: int
    slot_code: str
    product_id: Optional[int] = None
    stock: int = 0
    capacity: int = 10

class SlotOut(BaseModel):
    slot_id: int
    machine_id: int
    slot_code: str
    product_id: Optional[int]
    stock: int
    capacity: int
    created_at: datetime
    
    class Config:
        from_attributes = True