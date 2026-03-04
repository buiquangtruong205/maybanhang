"""
<<<<<<< HEAD
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
=======
Payment Schemas for PayOS integration
"""
from pydantic import BaseModel
from typing import Optional, List


class PaymentItem(BaseModel):
    """Item in payment request"""
    name: str
    quantity: int
    price: float  # Accept float from database Decimal values


class PaymentCreate(BaseModel):
    """Request body for creating payment link"""
    order_code: int
    amount: float  # Accept float, will be converted to int for PayOS
    description: str
    items: List[PaymentItem]
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_address: Optional[str] = None


class PaymentResponse(BaseModel):
    """Response after creating payment link"""
    success: bool
>>>>>>> origin/API_WEB_SERVER
    checkout_url: Optional[str] = None
    qr_code: Optional[str] = None
    error: Optional[str] = None


<<<<<<< HEAD
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
=======
class WebhookData(BaseModel):
    """PayOS webhook data structure"""
    orderCode: int
    amount: int
    description: str
    accountNumber: Optional[str] = None
    reference: Optional[str] = None
    transactionDateTime: Optional[str] = None
    currency: Optional[str] = None
    paymentLinkId: Optional[str] = None
    code: Optional[str] = None
    desc: Optional[str] = None
    counterAccountBankId: Optional[str] = None
    counterAccountBankName: Optional[str] = None
    counterAccountName: Optional[str] = None
    counterAccountNumber: Optional[str] = None
    virtualAccountName: Optional[str] = None
    virtualAccountNumber: Optional[str] = None


class WebhookPayload(BaseModel):
    """Full webhook payload from PayOS"""
    code: str
    desc: str
    success: bool
    data: Optional[WebhookData] = None
    signature: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Response for payment status check"""
    success: bool
    order_code: int
    status: str
    amount: Optional[int] = None
    amount_paid: Optional[int] = None
    amount_remaining: Optional[int] = None
    transactions: Optional[List[dict]] = None
    error: Optional[str] = None
>>>>>>> origin/API_WEB_SERVER
