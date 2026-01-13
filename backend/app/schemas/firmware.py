from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FirmwareUpdateCreate(BaseModel):
    machine_id: int
    from_version: Optional[str] = None
    to_version: str
    checksum: Optional[str] = None
    status: str = 'pending'


class FirmwareUpdateOut(BaseModel):
    update_id: int
    machine_id: int
    from_version: Optional[str]
    to_version: str
    checksum: Optional[str]
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class FirmwareUpdateStatus(BaseModel):
    status: str
    error_message: Optional[str] = None
