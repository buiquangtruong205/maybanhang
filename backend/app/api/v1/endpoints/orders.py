from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db.database import get_db
from app.services.order_service import OrderService
from app.api.v1.endpoints.auth import get_current_user

from app.services.payos_service import PayOSService
from app.services.product_service import ProductService

router = APIRouter()
payos_service = PayOSService()

# --- Public: check single order ---
@router.get("/{order_code}")
async def get_order_status(order_code: int, db: AsyncSession = Depends(get_db)):
    """Kiểm tra trạng thái đơn hàng và chủ động cập nhật từ PayOS nếu cần."""
    order = await OrderService.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    
    # Nếu đơn hàng đang PENDING, kiểm tra thực tế với PayOS
    if order.status == "PENDING":
        try:
            payment_info = await payos_service.get_payment_info(order_code)
            if payment_info.status == "PAID":
                order.status = "PAID"
                # Tự động trừ kho ngay khi xác nhận thanh toán thành công
                await ProductService.reduce_stock(db, order.product_id, order.machine_id)
                await db.commit()
                await db.refresh(order)
            elif payment_info.status == "CANCELLED":
                order.status = "CANCELLED"
                await db.commit()
                await db.refresh(order)
        except Exception as e:
            print(f"⚠️ Lỗi khi kiểm tra PayOS cho đơn hàng {order_code}: {e}")

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

@router.post("/{order_code}/manual-confirm")
async def manual_confirm_order(order_code: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Xác nhận đơn hàng thủ công (dành cho nhân viên)."""
    order = await OrderService.manual_confirm(db, order_code)
    if not order:
        raise HTTPException(status_code=400, detail="Không thể xác nhận đơn hàng này (Đơn hàng không tồn tại hoặc đã xử lý)")
    
    # Thực hiện trừ kho sau khi xác nhận thủ công
    try:
        await ProductService.reduce_stock(db, order.product_id, order.machine_id)
        await db.commit()
    except Exception as e:
        print(f"⚠️ Lỗi khi trừ kho đơn hàng {order_code}: {e}")
        
    return {"message": "Xác nhận đơn hàng thành công", "order_code": order_code}
