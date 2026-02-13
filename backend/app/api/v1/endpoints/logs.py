from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.database import get_db
from app.services.log_service import LogService
from app.api.v1.endpoints.auth import get_current_user, check_admin_role
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

from app.schemas.user import UserSchema
from app.schemas.machine import MachineSchema
from app.schemas.product import ProductInDB
from app.schemas.slot import SlotSchema

class RefillLogResponse(BaseModel):
    id: int
    user_id: int
    machine_id: int
    slot_id: int
    product_id: int
    quantity: int
    old_quantity: int
    new_quantity: int
    timestamp: datetime
    
    user: Optional[UserSchema] = None
    machine: Optional[MachineSchema] = None
    product: Optional[ProductInDB] = None
    slot: Optional[SlotSchema] = None

    class Config:
        from_attributes = True

@router.get("/refill", response_model=List[RefillLogResponse])
async def get_refill_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin_role)
):
    """Admin xem nhật ký nạp hàng."""
    return await LogService.get_refill_logs(db, skip=skip, limit=limit)
