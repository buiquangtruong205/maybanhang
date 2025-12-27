"""
Router xử lý các API sản phẩm
"""
from typing import List
from fastapi import APIRouter, HTTPException

from app.models.product import (
    Product, ProductResponse, 
    get_all_products, get_product_by_id, 
    update_product_stock, decrease_product_stock
)

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products", response_model=ProductResponse)
async def get_products():
    """Lấy danh sách tất cả sản phẩm"""
    try:
        products = get_all_products()
        return ProductResponse(
            success=True,
            data=products,
            message=f"Tìm thấy {len(products)} sản phẩm"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    """Lấy thông tin sản phẩm theo ID"""
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    return product


@router.put("/products/{product_id}/stock")
async def update_stock(product_id: int, new_stock: int):
    """Cập nhật stock sản phẩm"""
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock không thể âm")
    
    success = update_product_stock(product_id, new_stock)
    if not success:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    return {
        "success": True,
        "message": f"Đã cập nhật stock sản phẩm {product_id} thành {new_stock}"
    }


@router.post("/products/{product_id}/purchase")
async def purchase_product(product_id: int, quantity: int = 1):
    """Mua sản phẩm (giảm stock)"""
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Số lượng phải lớn hơn 0")
    
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    if product.stock < quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Không đủ hàng. Stock hiện tại: {product.stock}"
        )
    
    success = decrease_product_stock(product_id, quantity)
    if not success:
        raise HTTPException(status_code=500, detail="Lỗi cập nhật stock")
    
    return {
        "success": True,
        "message": f"Đã mua {quantity} {product.name}",
        "remaining_stock": product.stock
    }