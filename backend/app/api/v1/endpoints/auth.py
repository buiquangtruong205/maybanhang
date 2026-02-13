from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import UserRole
from app.services.user_service import UserService
from app.core.security import (
    create_access_token, 
    verify_password, 
    get_current_user
)

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Đăng nhập hệ thống sử dụng UserService."""
    user = await UserService.get_user_by_username(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "id": user.id, 
            "username": user.username, 
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.get("/me")
async def read_users_me(current_user: tuple = Depends(get_current_user)):
    """Lấy thông tin người dùng hiện tại."""
    return current_user

async def check_admin_role(current_user = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires ADMIN privileges"
        )
    return current_user

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str = ""

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Đăng ký tài khoản mới sử dụng UserService."""
    existing = await UserService.get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    user_data = req.model_dump()
    user_data["role"] = UserRole.ADMIN # Mặc định Admin cho giai đoạn setup
    
    user = await UserService.create_user(db, user_data)
    return {"id": user.id, "username": user.username, "message": "Đăng ký thành công", "role": user.role}
