from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.product import Product
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

# --- Schemas ---
class ProductCreate(BaseModel):
    name: str
    price: int
    image_url: str = ""
    description: str = ""
    category: str = "drink"
    is_available: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None

# --- Public endpoints (for customer) ---

@router.get("/", response_description="List all products")
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    products = result.scalars().all()
    return products

@router.get("/{product_id}", response_description="Get a single product")
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# --- Admin endpoints (protected) ---

@router.post("/", response_description="Create a new product")
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@router.put("/{product_id}", response_description="Update a product")
async def update_product(product_id: int, product: ProductUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)

    await db.commit()
    await db.refresh(existing)
    return existing

@router.delete("/{product_id}", response_description="Delete a product")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(existing)
    await db.commit()
    return {"message": "Đã xóa sản phẩm", "id": product_id}