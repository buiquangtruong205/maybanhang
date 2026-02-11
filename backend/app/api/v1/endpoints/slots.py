from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.slot import Slot
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

class SlotCreate(BaseModel):
    machine_id: int
    slot_code: str  # A1, A2, B1...
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
    query = select(Slot)
    if machine_id:
        query = query.where(Slot.machine_id == machine_id)
    result = await db.execute(query)
    slots = result.scalars().all()
    return slots

@router.get("/{slot_id}")
async def get_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot

# --- Admin ---
@router.post("/")
async def create_slot(slot: SlotCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    new_slot = Slot(**slot.model_dump())
    db.add(new_slot)
    await db.commit()
    await db.refresh(new_slot)
    return new_slot

@router.put("/{slot_id}")
async def update_slot(slot_id: int, slot: SlotUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Slot not found")

    update_data = slot.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)

    await db.commit()
    await db.refresh(existing)
    return existing

@router.delete("/{slot_id}")
async def delete_slot(slot_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Slot not found")

    await db.delete(existing)
    await db.commit()
    return {"message": "Đã xóa slot", "id": slot_id}
