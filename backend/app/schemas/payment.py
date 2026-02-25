"""
Schemas cho thanh toán (Payment).
Dùng để validate request/response cho PayOS integration.
"""
from pydantic import BaseModel
from typing import Optional


# === Request Schemas ===

class PaymentCreate(BaseModel):
    """Schema khi frontend yêu cầu tạo link thanh toán."""
    product_id: int
    machine_id: int = 1
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


# === Response Schemas ===

class PaymentResponse(BaseModel):
    """Schema trả về sau khi tạo link thanh toán PayOS thành công."""
    success: bool
    order_code: Optional[int] = None
    checkout_url: Optional[str] = None
    qr_code: Optional[str] = None
    error: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Schema trả về trạng thái thanh toán."""
    order_code: int
    status: str
    amount: Optional[int] = None


# === Webhook Schemas ===

class WebhookPayload(BaseModel):
    """Schema cho PayOS webhook callback.
    PayOS gửi POST request tới backend khi thanh toán hoàn tất.
    """
    code: str
    desc: str
    success: bool
    data: Optional[dict] = None
    signature: Optional[str] = None
