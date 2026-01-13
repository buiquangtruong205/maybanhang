from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    product_name: str
    price: float
    image: Optional[str] = None
    active: bool = True

class ProductOut(BaseModel):
    product_id: int
    product_name: str
    price: float
    image: Optional[str]
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True