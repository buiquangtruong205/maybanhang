from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from app.db.database import get_db
from app.models.product import Product
from app.models.slot import Slot
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.product import ProductCreate, ProductUpdate, ProductWithStock

router = APIRouter()

# --- Public endpoints (for customer) ---

@router.get("/", response_model=List[ProductWithStock], response_description="List all products with stock")
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Calculate total stock for each product by summing up slots
    stmt = (
        select(Product, func.coalesce(func.sum(Slot.stock), 0).label("stock"))
        .outerjoin(Slot, Slot.product_id == Product.id)
        .group_by(Product.id)
        .offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    # Map to schema
    products = []
    for product, stock in rows:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "image_url": product.image_url,
            "description": product.description,
            "category": product.category,
            "is_available": product.is_available,
            "stock": stock
        }
        products.append(product_dict)
        
    return products

@router.get("/{product_id}", response_model=ProductWithStock, response_description="Get a single product with stock")
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Product, func.coalesce(func.sum(Slot.stock), 0).label("stock"))
        .outerjoin(Slot, Slot.product_id == Product.id)
        .where(Product.id == product_id)
        .group_by(Product.id)
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product, stock = row
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "image_url": product.image_url,
        "description": product.description,
        "category": product.category,
        "is_available": product.is_available,
        "stock": stock
    }

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