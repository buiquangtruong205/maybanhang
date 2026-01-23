from datetime import datetime
from pydantic import BaseModel
from typing import Optional


# DeviceIdentity Schemas
class DeviceIdentityCreate(BaseModel):
    machine_id: int
    device_public_key: Optional[str] = None
    cert_fingerprint: Optional[str] = None
    secure_element_id: Optional[str] = None
    mac_address: Optional[str] = None
    status: str = 'active'


class DeviceIdentityOut(BaseModel):
    machine_id: int
    device_public_key: Optional[str]
    cert_fingerprint: Optional[str]
    secure_element_id: Optional[str]
    mac_address: Optional[str]
    provisioned_at: datetime
    revoked_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


# DeviceSession Schemas
class DeviceSessionCreate(BaseModel):
    machine_id: int
    token_hash: str
    expires_at: datetime
    ip_address: Optional[str] = None


class DeviceSessionOut(BaseModel):
    session_id: int
    machine_id: int
    token_hash: str
    issued_at: datetime
    expires_at: datetime
    last_seen_at: Optional[datetime]
    ip_address: Optional[str]
    is_revoked: bool

    class Config:
        from_attributes = True



