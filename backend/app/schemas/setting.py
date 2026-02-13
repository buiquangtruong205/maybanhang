from pydantic import BaseModel
from typing import Optional

class SettingBase(BaseModel):
    key: str
    value: Optional[str] = None
    type: str = "string"
    description: Optional[str] = None
    group: str = "general"

class SettingUpdate(BaseModel):
    value: str

class SettingResponse(SettingBase):
    class Config:
        from_attributes = True
