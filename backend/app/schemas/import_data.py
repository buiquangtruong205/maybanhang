from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ImportDataCreate(BaseModel):
    user_id: int
    machine_id: int
    slot_id: int
    product_id: int
    quantity: int


class ImportDataOut(BaseModel):
    import_id: int
    user_id: int
    machine_id: int
    slot_id: int
    product_id: int
    quantity: int
    created_at: datetime

    class Config:
        from_attributes = True
