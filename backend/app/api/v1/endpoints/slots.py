from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel

from app.db.database import get_db
from app.services.slot_service import SlotService
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

class SlotCreate(BaseModel):
    machine_id: int
    slot_code: str
    product_id: Optional[int] = None
    stock: int = 0
    capacity: int = 10

class SlotUpdate(BaseModel):
    product_id: Optional[int] = None
    stock: Optional[int] = None
    capacity: Optional[int] = None

# --- Public: get slots by machine ---
@router.get("/")
async def list_slots(machine_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Liệt kê danh sách slot dùng SlotService."""
    return await SlotService.list_slots(db, machine_id=machine_id)

@router.get("/{slot_id}")
async def get_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    """Lấy chi tiết slot dùng SlotService."""
    slot = await SlotService.get_slot_by_id(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí (slot) này")
    return slot

# --- Admin ---
@router.post("/")
async def create_slot(slot: SlotCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Tạo slot mới dùng SlotService."""
    return await SlotService.create_slot(db, slot.model_dump())

@router.put("/{slot_id}")
async def update_slot(slot_id: int, slot: SlotUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Cập nhật slot dùng SlotService."""
    updated = await SlotService.update_slot(db, slot_id, slot.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí (slot) này")
    return updated

@router.delete("/{slot_id}")
async def delete_slot(slot_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Xóa slot dùng SlotService."""
    success = await SlotService.delete_slot(db, slot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí (slot) này")
    return {"message": "Đã xóa vị trí (slot) thành công", "id": slot_id}
