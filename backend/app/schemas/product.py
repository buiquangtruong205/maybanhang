from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    price: float
    image: Optional[str] = None
    active: bool = True

class ProductOut(BaseModel):
    product_id: int
    name: str
    price: float
    image: Optional[str]
    active: bool
    
    class Config:
        from_attributes = True