from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.database import get_db
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.machine import Machine
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/")
async def read_stats(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    # Total revenue (COMPLETED orders)
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED)
    )
    total_revenue = revenue_result.scalar()

    # Order counts
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar()
    paid_orders = (await db.execute(select(func.count(Order.id)).where(Order.status == OrderStatus.PAID))).scalar()
    completed_orders = (await db.execute(select(func.count(Order.id)).where(Order.status == OrderStatus.COMPLETED))).scalar()
    pending_orders = (await db.execute(select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING))).scalar()

    # Products & Machines
    total_products = (await db.execute(select(func.count(Product.id)))).scalar()
    total_machines = (await db.execute(select(func.count(Machine.id)))).scalar()
    online_machines = (await db.execute(
        select(func.count(Machine.id)).where(Machine.status == "online")
    )).scalar()

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "total_products": total_products,
        "total_machines": total_machines,
        "online_machines": online_machines,
    }
