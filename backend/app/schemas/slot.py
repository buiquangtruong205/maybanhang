from pydantic import BaseModel
from typing import Optional

class SlotBase(BaseModel):
    slot_id: str
    capacity: int
    current_quantity: int = 0
    is_active: bool = True

class SlotCreate(SlotBase):
    machine_id: int
    product_id: Optional[int] = None

class SlotUpdate(BaseModel):
    capacity: Optional[int] = None
    current_quantity: Optional[int] = None
    is_active: Optional[bool] = None
    product_id: Optional[int] = None

class SlotSchema(SlotBase):
    id: int
    machine_id: int
    product_id: Optional[int] = None

    class Config:
        from_attributes = True
