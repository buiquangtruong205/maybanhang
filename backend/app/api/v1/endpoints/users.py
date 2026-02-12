from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import text

from app.db.database import get_db, engine, Base
from app.models.user import User, UserRole
from app.core.security import get_current_active_admin, get_password_hash

router = APIRouter()

# --- Schemas ---
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    full_name: str = ""
    role: UserRole = UserRole.STAFF

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role: UserRole

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.post("/reset-admin-db")
async def reset_admin_db(db: AsyncSession = Depends(get_db)):
    try:
        # 1. Drop Table & Type
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            try:
                await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
            except Exception:
                pass
        
        # 2. Create Table
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # 3. Seed Admin
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrator",
            role=UserRole.ADMIN
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        return {"message": "Admin Reset Successful", "user": admin}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=UserResponse)
async def create_user(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    # Check username
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_in: UserUpdate, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        if user.id == admin.id and user_in.role != UserRole.ADMIN:
             raise HTTPException(status_code=400, detail="Cannot demote yourself")
        user.role = user_in.role
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
        
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
):
    if user_id == admin.id:
         raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}
