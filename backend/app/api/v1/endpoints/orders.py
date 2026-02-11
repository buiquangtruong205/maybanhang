from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.order import Order, OrderStatus
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

# --- Public: check single order ---
@router.get("/{order_code}")
async def get_order_status(order_code: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.order_code == order_code))
    order = result.scalar_one_or_none()
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
    query = select(Order).order_by(Order.created_at.desc())
    if status:
        query = query.where(Order.status == status)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "order_code": o.order_code,
            "product_id": o.product_id,
            "machine_id": o.machine_id,
            "amount": o.amount,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]
