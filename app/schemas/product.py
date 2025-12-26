from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    price: float
    image: Optional[str] = None  # URL hoặc path của ảnh sản phẩm
    active: bool = True

class ProductOut(ProductCreate):
    id: int
    
    class Config:
        from_attributes = True