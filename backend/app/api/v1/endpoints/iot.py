from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.db.database import get_db
from app.models.order import Order, OrderStatus

router = APIRouter()

class DispenseRequest(BaseModel):
    order_code: int
    success: bool

@router.get("/check-order/{order_code}")
async def check_order_iot(
    order_code: int, 
    x_machine_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Verify Machine Key (TODO: Check against DB)
    if x_machine_key not in ["may1", "may2", "may3"]:
         raise HTTPException(status_code=403, detail="Invalid Machine Key")

    result = await db.execute(select(Order).where(Order.order_code == order_code))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return {
        "order_code": order.order_code,
        "status": order.status,
        "should_dispense": order.status == OrderStatus.PAID
    }

@router.post("/dispense-complete")
async def dispense_complete(
    request: DispenseRequest,
    x_machine_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Verify Machine Key
    if x_machine_key not in ["may1", "may2", "may3"]:
         raise HTTPException(status_code=403, detail="Invalid Machine Key")
         
    result = await db.execute(select(Order).where(Order.order_code == request.order_code))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if request.success:
        order.status = OrderStatus.COMPLETED
    else:
        order.status = OrderStatus.FAILED
        
    await db.commit()
    
    return {"success": True, "status": order.status}
