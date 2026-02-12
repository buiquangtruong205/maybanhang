from sqlalchemy import Column, Integer, String, Boolean, Enum as SqlEnum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    role = Column(SqlEnum(UserRole), default=UserRole.STAFF)
