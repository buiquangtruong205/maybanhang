from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from typing import Optional

class SlotCreate(BaseModel):
    machine_id: int
    slot_code: str
    product_id: Optional[int] = None
    stock: int = 0
    capacity: int = Field(10, ge=1)

    @model_validator(mode='after')
    def stock_not_exceed_capacity(self):
        if self.stock > self.capacity:
            raise ValueError(
                f'Số lượng tồn kho ({self.stock}) không được vượt quá sức chứa ({self.capacity})'
            )
        return self

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