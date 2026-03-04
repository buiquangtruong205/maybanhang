<<<<<<< HEAD
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
=======
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
>>>>>>> origin/API_WEB_SERVER
