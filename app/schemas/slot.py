from typing import Optional
from pydantic import BaseModel
from app.schemas.product import ProductOut

class SlotCreate(BaseModel):
    machine_id: int
    slot_no: str
    product_id: int
    quantity: int

class SlotOut(SlotCreate):
    id: int
    product: Optional[ProductOut] = None
    
    class Config:
        from_attributes = True