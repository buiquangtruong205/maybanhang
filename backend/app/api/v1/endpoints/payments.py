from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import random
import time

from app.db.database import get_db
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.machine import Machine
from app.services.payos_service import PayOSService

router = APIRouter()
payos_service = PayOSService()

class CreatePaymentRequest(BaseModel):
    product_id: int
    machine_id: int = 1 # Default to VM001 for now

@router.post("/create")
async def create_payment(request: CreatePaymentRequest, db: AsyncSession = Depends(get_db)):
    # 1. Get Product
    result = await db.execute(select(Product).where(Product.id == request.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 2. Get Machine (Optional check)
    # ...

    # 3. Create Order in DB (Pending)
    order_code = int(time.time()) # Simple order code
    new_order = Order(
        order_code=order_code,
        product_id=product.id,
        machine_id=request.machine_id,
        amount=product.price,
        status=OrderStatus.PENDING
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    # 4. Create PayOS Payment Link
    try:
        payment_data = await payos_service.create_payment_link(
            order_code=order_code,
            amount=product.price,
            description=f"Mua {product.name}",
            return_url=f"/success",
            cancel_url=f"/cancel"
        )
        
        # 5. Update Order with PayOS data
        new_order.payment_url = payment_data.get("checkoutUrl")
        new_order.qr_code = payment_data.get("qrCode")
        await db.commit()
        
        return {
            "order_code": order_code,
            "checkout_url": new_order.payment_url,
            "qr_code": new_order.qr_code
        }
        
    except Exception as e:
        print(f"PayOS Error: {e}")
        # If PayOS fails, still return order but with error? Or raise HTTP 500?
        # For now raise 500
        raise HTTPException(status_code=500, detail=str(e))
