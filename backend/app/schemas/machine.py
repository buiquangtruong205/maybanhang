from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class MachineCreate(BaseModel):
    name: str
    location: Optional[str] = None
    status: str = 'active'
    secret_key: Optional[str] = None

class MachineOut(BaseModel):
    machine_id: int
    name: str
    location: Optional[str]
    status: str
    secret_key: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
