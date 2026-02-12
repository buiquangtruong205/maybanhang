from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.issue import IssueStatus

class IssueBase(BaseModel):
    machine_id: Optional[int] = None
    content: str

class IssueCreate(IssueBase):
    pass

class IssueUpdate(BaseModel):
    status: Optional[IssueStatus] = None

class IssueSchema(IssueBase):
    id: int
    user_id: int
    status: IssueStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
