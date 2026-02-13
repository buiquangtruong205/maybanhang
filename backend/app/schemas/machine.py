from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.machine import MachineStatus

class MachineBase(BaseModel):
    name: str
    location: Optional[str] = None
    status: Optional[MachineStatus] = MachineStatus.ONLINE

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[MachineStatus] = None

class MachineSchema(MachineBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
