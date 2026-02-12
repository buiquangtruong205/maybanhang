from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.payos_service import PayOSService

router = APIRouter()
payos_service = PayOSService()

class CreatePaymentRequest(BaseModel):
    product_id: int
    machine_id: int = 1

@router.post("/create")
async def create_payment(request: CreatePaymentRequest, db: AsyncSession = Depends(get_db)):
    """Khởi tạo thanh toán và đơn hàng thông qua các Service chuyên biệt."""
    # 1. Get Product
    product = await ProductService.get_product_by_id(db, request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    # 2. Check stock
    has_stock = await ProductService.check_stock(db, request.product_id, request.machine_id)
    if not has_stock:
        raise HTTPException(status_code=400, detail="Sản phẩm đã hết hàng tại máy này")

    # 3. Create Order in DB (Pending) using OrderService
    new_order = await OrderService.create_new_order(
        db, 
        product_id=product.id, 
        machine_id=request.machine_id, 
        amount=product.price
    )

    # 4. Create PayOS Payment Link
    try:
        payment_data = await payos_service.create_payment_link(
            order_code=new_order.order_code,
            amount=product.price,
            description=f"Mua {product.name}",
            return_url=f"/success",
            cancel_url=f"/cancel"
        )
        
        # 5. Update Order with PayOS data
        # Note: We use dynamic assignment here, ensuring consistency in DB
        new_order.payment_url = payment_data.get("checkoutUrl")
        new_order.qr_code = payment_data.get("qrCode")
        await db.commit()
        
        return {
            "order_code": new_order.order_code,
            "checkout_url": new_order.payment_url,
            "qr_code": new_order.qr_code
        }
        
    except Exception as e:
        print(f"PayOS Error: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi cổng thanh toán PayOS: {str(e)}")
