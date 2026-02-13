from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class IssueStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    content = Column(String, nullable=False)
    status = Column(String, default=IssueStatus.OPEN.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    machine = relationship("Machine")
