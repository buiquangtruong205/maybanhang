from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.machine import Machine
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
    result = await db.execute(select(Machine).offset(skip).limit(limit))
    machines = result.scalars().all()
    return machines

@router.get("/{machine_id}", response_description="Get a single machine")
async def read_machine(machine_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

# --- Admin ---
@router.post("/", response_description="Create a machine")
async def create_machine(machine: MachineCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    new_machine = Machine(**machine.model_dump())
    db.add(new_machine)
    await db.commit()
    await db.refresh(new_machine)
    return new_machine

@router.put("/{machine_id}", response_description="Update a machine")
async def update_machine(machine_id: int, machine: MachineUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Machine not found")

    update_data = machine.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)

    await db.commit()
    await db.refresh(existing)
    return existing

@router.delete("/{machine_id}", response_description="Delete a machine")
async def delete_machine(machine_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Machine not found")

    await db.delete(existing)
    await db.commit()
    return {"message": "Đã xóa máy", "id": machine_id}
