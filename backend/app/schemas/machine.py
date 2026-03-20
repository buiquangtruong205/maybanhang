from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Optional

class MachineCreate(BaseModel):
    name: str
    location: Optional[str] = None
    status: str = 'active'
    secret_key: str = Field(min_length=1)
    mqtt_command_topic: Optional[str] = None
    mqtt_status_topic: Optional[str] = None
    mqtt_broadcast_status_topic: Optional[str] = None
    ui_layout: Optional[dict[str, Any]] = None
    device_profile: Optional[dict[str, Any]] = None
    config_notes: Optional[str] = None

class MachineOut(BaseModel):
    machine_id: int
    name: str
    location: Optional[str]
    status: str
    secret_key: Optional[str]
    mqtt_command_topic: Optional[str]
    mqtt_status_topic: Optional[str]
    mqtt_broadcast_status_topic: Optional[str]
    ui_layout: Optional[dict[str, Any]]
    device_profile: Optional[dict[str, Any]]
    config_notes: Optional[str]
    created_at: datetime
    
    # Dynamic status from DeviceIdentity
    wifi_status: Optional[str] = "disconnected"
    wifi_signal: Optional[str] = None
    uptime: Optional[int] = 0
    
    class Config:
        from_attributes = True
