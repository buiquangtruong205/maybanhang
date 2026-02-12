from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db.database import get_db
from app.services.order_service import OrderService
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

# --- Public: check single order ---
@router.get("/{order_code}")
async def get_order_status(order_code: int, db: AsyncSession = Depends(get_db)):
    """Kiểm tra trạng thái đơn hàng thông qua OrderService."""
    order = await OrderService.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_code": order.order_code,
        "status": order.status,
        "amount": order.amount,
        "qr_code": order.qr_code,
        "payment_url": order.payment_url
    }

# --- Admin: list all orders ---
@router.get("/")
async def list_orders(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user)
):
    """Liệt kê danh sách đơn hàng dùng OrderService."""
    orders = await OrderService.list_orders(db, skip=skip, limit=limit, status=status)
    return orders
