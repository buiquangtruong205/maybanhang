"""
Payment Schemas for PayOS integration
"""
from pydantic import BaseModel
from typing import Optional, List


class PaymentItem(BaseModel):
    """Item in payment request"""
    name: str
    quantity: int
    price: int


class PaymentCreate(BaseModel):
    """Request body for creating payment link"""
    order_code: int
    amount: int
    description: str
    items: List[PaymentItem]
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_address: Optional[str] = None


class PaymentResponse(BaseModel):
    """Response after creating payment link"""
    success: bool
    checkout_url: Optional[str] = None
    qr_code: Optional[str] = None
    error: Optional[str] = None


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
