"""
Router xử lý các API thanh toán
"""
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.services.payos_service import create_payment_link
from app.models.product import get_product_by_id

router = APIRouter()


class CreatePaymentRequest(BaseModel):
    """Request model cho tạo thanh toán"""
    machine_id: str
    product_id: int
    amount: int


class PaymentResponse(BaseModel):
    """Response model cho thanh toán"""
    success: bool
    order_code: int
    checkout_url: str = None
    qr_url: str = None
    message: str = None


@router.post("/api/create-payment", response_model=PaymentResponse)
async def create_payment_api(request: CreatePaymentRequest):
    """API tạo thanh toán cho sản phẩm"""
    # Kiểm tra sản phẩm tồn tại
    product = get_product_by_id(request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    
    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="Sản phẩm đã hết hàng")
    
    # Tạo order code
    order_code = int(time.time())
    
    # Tạo items cho PayOS
    items = [{
        "name": product.name,
        "quantity": 1,
        "price": product.price
    }]
    
    # Tạo payment link
    result = create_payment_link(
        order_code=order_code,
        amount=request.amount,
        description=f"Mua {product.name} - Máy {request.machine_id}",
        items=items
    )
    
    if result["success"]:
        return PaymentResponse(
            success=True,
            order_code=order_code,
            checkout_url=result["checkout_url"],
            qr_url=result.get("qr_url"),
            message="Tạo thanh toán thành công"
        )
    else:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo thanh toán: {result['error']}")


@router.get("/api/order-status/{order_code}")
async def get_order_status(order_code: int):
    """Kiểm tra trạng thái đơn hàng"""
    # TODO: Implement order status check with database
    # Hiện tại trả về PENDING để test
    return {
        "success": True,
        "order_code": order_code,
        "status": "PENDING",
        "message": "Đang chờ thanh toán"
    }


@router.post("/api/dispense-complete")
async def dispense_complete(data: dict):
    """Xác nhận xuất hàng thành công"""
    # TODO: Implement dispense confirmation logic
    return {
        "success": True,
        "message": "Đã xác nhận xuất hàng thành công"
    }


@router.post("/api/heartbeat")
async def machine_heartbeat(data: dict):
    """Nhận heartbeat từ máy bán hàng"""
    # TODO: Implement machine status tracking
    return {
        "success": True,
        "message": "Heartbeat received"
    }


@router.get("/", response_class=HTMLResponse)
async def home():
    """Trang chủ với form thanh toán demo"""
    return """
    <html>
        <head>
            <title>Demo PayOS</title>
            <meta charset="utf-8">
        </head>
        <body style="font-family:sans-serif; text-align:center; padding-top:50px; background:#f5f5f5;">
            <div style="padding: 30px; border: 1px solid #ddd; display: inline-block; border-radius: 15px; background:white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1 style="color:#333;">🏪 Cửa hàng Demo</h1>
                <p style="font-size:18px;">Giá: <b style="color:#e74c3c;">10,000 VND</b></p>
                <form action="/create-payment" method="post">
                    <button style="padding:15px 30px; background:#3498db; color:white; border:none; border-radius:8px; cursor:pointer; font-size:16px; transition: background 0.3s;" 
                            onmouseover="this.style.background='#2980b9'" 
                            onmouseout="this.style.background='#3498db'" 
                            type="submit">
                        💳 Thanh toán QR
                    </button>
                </form>
            </div>
        </body>
    </html>
    """


@router.post("/create-payment")
async def create_payment():
    """Tạo thanh toán và redirect đến PayOS"""
    order_code = int(time.time())
    items = [{"name": "Gói Premium", "quantity": 1, "price": 10000}]
    
    result = create_payment_link(
        order_code=order_code,
        amount=10000,
        description=f"Thanh toan {order_code}",
        items=items
    )
    
    if result["success"]:
        return RedirectResponse(url=result["checkout_url"], status_code=303)
    else:
        return {"error": result["error"]}


@router.get("/success", response_class=HTMLResponse)
async def success():
    """Trang thông báo thanh toán thành công"""
    return """
    <html>
        <head><title>Thành công</title><meta charset="utf-8"></head>
        <body style="font-family:sans-serif; text-align:center; padding-top:100px; background:#d4edda;">
            <h1 style="color:#155724; font-size:48px;">✅</h1>
            <h1 style="color:#155724;">Thanh toán thành công!</h1>
            <p>Cảm ơn bạn đã sử dụng dịch vụ.</p>
            <a href="/" style="color:#3498db;">← Quay về trang chủ</a>
        </body>
    </html>
    """


@router.get("/cancel", response_class=HTMLResponse)
async def cancel():
    """Trang thông báo đã hủy thanh toán"""
    return """
    <html>
        <head><title>Đã hủy</title><meta charset="utf-8"></head>
        <body style="font-family:sans-serif; text-align:center; padding-top:100px; background:#f8d7da;">
            <h1 style="color:#721c24; font-size:48px;">❌</h1>
            <h1 style="color:#721c24;">Đã hủy thanh toán!</h1>
            <p>Bạn có thể thử lại bất cứ lúc nào.</p>
            <a href="/" style="color:#3498db;">← Quay về trang chủ</a>
        </body>
    </html>
    """
