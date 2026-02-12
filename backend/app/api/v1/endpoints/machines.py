from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel

from app.db.database import get_db
from app.services.machine_service import MachineService
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

class MachineCreate(BaseModel):
    name: str
    location: str = ""
    status: str = "online"
    secret_key: str = ""

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    secret_key: Optional[str] = None

# --- Public ---
@router.get("/", response_description="List all machines")
async def read_machines(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Liệt kê danh sách máy dùng MachineService."""
    return await MachineService.list_machines(db, skip=skip, limit=limit)

@router.get("/{machine_id}", response_description="Get a single machine")
async def read_machine(machine_id: int, db: AsyncSession = Depends(get_db)):
    """Lấy chi tiết máy dùng MachineService."""
    machine = await MachineService.get_machine_by_id(db, machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

# --- Admin ---
@router.post("/", response_description="Create a machine")
async def create_machine(machine: MachineCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Tạo máy mới dùng MachineService."""
    return await MachineService.create_machine(db, machine.model_dump())

@router.put("/{machine_id}", response_description="Update a machine")
async def update_machine(machine_id: int, machine: MachineUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Cập nhật máy dùng MachineService."""
    updated = await MachineService.update_machine(db, machine_id, machine.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Machine not found")
    return updated

@router.delete("/{machine_id}", response_description="Delete a machine")
async def delete_machine(machine_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    """Xóa máy dùng MachineService."""
    success = await MachineService.delete_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": "Đã xóa máy", "id": machine_id}
