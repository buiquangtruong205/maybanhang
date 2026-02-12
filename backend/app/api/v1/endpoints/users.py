from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import text

from app.db.database import get_db, engine, Base
from app.models.user import User, UserRole
from app.services.user_service import UserService
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
    """Xử lý reset database và tạo admin mặc định (Dùng cho phát triển)."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            try:
                await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
            except Exception: pass
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        await UserService.create_user(db, {
            "username": "admin",
            "password": "admin123",
            "full_name": "Administrator",
            "role": UserRole.ADMIN
        })
        
        return {"message": "Reset dữ liệu Admin thành công"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    """Liệt kê người dùng dùng UserService."""
    return await UserService.list_users(db, skip=skip, limit=limit)

@router.post("/", response_model=UserResponse)
async def create_user(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    """Tạo người dùng dùng UserService."""
    existing = await UserService.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    return await UserService.create_user(db, user_in.model_dump())

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_in: UserUpdate, 
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    """Cập nhật người dùng dùng UserService."""
    # Kiểm tra không cho Admin tự hạ quyền của chính mình
    if user_id == admin.id and user_in.role and user_in.role != UserRole.ADMIN:
         raise HTTPException(status_code=400, detail="Bạn không thể tự hạ quyền của chính mình")

    updated = await UserService.update_user(db, user_id, user_in.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    return updated

@router.delete("/{user_id}")
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    """Xóa người dùng dùng UserService."""
    if user_id == admin.id:
         raise HTTPException(status_code=400, detail="Bạn không thể tự xóa tài khoản của chính mình")

    success = await UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        
    return {"message": "Đã xóa người dùng thành công"}
