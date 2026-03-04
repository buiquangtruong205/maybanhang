from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class SlotCreate(BaseModel):
    machine_id: int
    slot_code: str
    product_id: Optional[int] = None
    stock: int = 0
    capacity: int = Field(10, ge=0, le=10)

    @root_validator
    def stock_not_exceed_capacity(cls, values):
        stock = values.get('stock', 0)
        cap = values.get('capacity', 0)
        if stock > cap:
            raise ValueError('stock cannot exceed capacity')
        return values

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