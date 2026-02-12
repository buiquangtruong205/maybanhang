from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.services.product_service import ProductService
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.product import ProductCreate, ProductUpdate, ProductWithStock

router = APIRouter()

# --- Public endpoints (for customer) ---

@router.get("/", response_model=List[ProductWithStock], response_description="List all products with stock")
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Lấy danh sách sản phẩm thông qua ProductService."""
    return await ProductService.get_all_products(db, skip=skip, limit=limit)

@router.get("/{product_id}", response_model=ProductWithStock, response_description="Get a single product with stock")
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Lấy chi tiết sản phẩm thông qua ProductService."""
    product = await ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# --- Admin endpoints (protected) ---

@router.post("/", response_description="Create a new product")
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Tạo sản phẩm mới dùng ProductService."""
    return await ProductService.create_product(db, product.model_dump())

@router.put("/{product_id}", response_description="Update a product")
async def update_product(product_id: int, product: ProductUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Cập nhật sản phẩm dùng ProductService."""
    updated = await ProductService.update_product(db, product_id, product.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated

@router.delete("/{product_id}", response_description="Delete a product")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Xóa sản phẩm dùng ProductService."""
    success = await ProductService.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Đã xóa sản phẩm", "id": product_id}