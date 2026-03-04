<<<<<<< HEAD
from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    price: int
    image_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "drink"
    is_available: Optional[bool] = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None

class ProductInDB(ProductBase):
    id: int

    class Config:
        from_attributes = True

class ProductWithStock(ProductInDB):
    stock: int = 0
=======
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
    stock: int
    created_at: datetime
    
    class Config:
        from_attributes = True
>>>>>>> origin/API_WEB_SERVER
