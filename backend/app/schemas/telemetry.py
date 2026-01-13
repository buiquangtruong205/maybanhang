from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any


class TelemetryLogCreate(BaseModel):
    machine_id: int
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    voltage: Optional[float] = None
    door_open: Optional[bool] = None
    metrics_json: Optional[Any] = None


class TelemetryLogOut(BaseModel):
    log_id: int
    machine_id: int
    ts: datetime
    temperature: Optional[float]
    humidity: Optional[float]
    voltage: Optional[float]
    door_open: Optional[bool]
    metrics_json: Optional[Any]

    class Config:
        from_attributes = True
