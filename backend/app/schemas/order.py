<<<<<<< HEAD
"""
Schemas cho đơn hàng (Order).
Dùng để validate request/response trong API endpoints.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# === Request Schemas ===

class OrderCreate(BaseModel):
    """Schema khi tạo đơn hàng mới từ frontend."""
    product_id: int
    machine_id: int = 1


class OrderManualConfirm(BaseModel):
    """Schema khi nhân viên xác nhận đơn hàng thủ công."""
    order_code: int


# === Response Schemas ===

class OrderResponse(BaseModel):
    """Schema trả về thông tin đơn hàng."""
    id: int
    order_code: int
    product_id: int
    machine_id: int
    amount: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Schema trả về danh sách đơn hàng có phân trang."""
    orders: list[OrderResponse]
    total: int
    skip: int
    limit: int


class OrderStatusUpdate(BaseModel):
    """Schema khi cập nhật trạng thái đơn hàng."""
    status: str
=======
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class OrderCreate(BaseModel):
    product_id: int
    price_snapshot: float
    slot_id: Optional[int] = None  # Optional for demo without slots
    status_payment: str = 'pending'
    status_slots: str = 'pending'

class OrderOut(BaseModel):
    order_id: int
    product_id: int
    price_snapshot: float
    slot_id: Optional[int] = None  # Optional for demo without slots
    status_payment: str
    status_slots: str
    created_at: datetime
    
    class Config:
        from_attributes = True
>>>>>>> origin/API_WEB_SERVER
