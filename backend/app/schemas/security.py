from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any


# SecurityEvent Schemas
class SecurityEventCreate(BaseModel):
    machine_id: Optional[int] = None
    event_type: str
    severity: str = 'low'
    message: Optional[str] = None
    detail_json: Optional[Any] = None


class SecurityEventOut(BaseModel):
    event_id: int
    machine_id: Optional[int]
    event_type: str
    severity: str
    message: Optional[str]
    detail_json: Optional[Any]
    created_at: datetime
    is_resolved: bool
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


# ApiAuditLog Schemas
class ApiAuditLogCreate(BaseModel):
    machine_id: Optional[int] = None
    endpoint: str
    method: str
    ip_address: Optional[str] = None
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
    user_id: Optional[int] = None
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
