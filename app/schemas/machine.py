from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class MachineCreate(BaseModel):
    name: str
    location: Optional[str] = None
    status: Optional[str] = 'active'

class MachineOut(BaseModel):
    id: int
    name: str
    location: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
