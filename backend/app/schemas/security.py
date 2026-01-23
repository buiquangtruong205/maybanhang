from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ApiAuditLog Schemas
class ApiAuditLogCreate(BaseModel):
    machine_id: Optional[int]
    endpoint: str
    method: str
    ip_address: Optional[str]
    response_code: int
    payload_hash: Optional[str] = None
    signature_ok: bool = False


class ApiAuditLogOut(BaseModel):
    request_id: int
    machine_id: Optional[int]
    endpoint: str
    method: str
    ip_address: Optional[str]
    response_code: int
    payload_hash: Optional[str]
    signature_ok: bool
    created_at: datetime

    class Config:
        from_attributes = True


# StaffAccessLog Schemas
class StaffAccessLogCreate(BaseModel):
    user_id: Optional[int]
    machine_id: int
    action: str
    note: Optional[str] = None


class StaffAccessLogOut(BaseModel):
    access_id: int
    user_id: Optional[int]
    machine_id: int
    action: str
    started_at: datetime
    ended_at: Optional[datetime]
    note: Optional[str]

    class Config:
        from_attributes = True


class StaffAccessLogEnd(BaseModel):
    note: Optional[str] = None
