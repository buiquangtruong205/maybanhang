from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import User, UserRole
from app.core.security import (
    create_access_token, 
    verify_password, 
    get_password_hash, 
    get_current_user
)

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Authenticate user
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

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
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id, 
        "username": current_user.username, 
        "full_name": current_user.full_name,
        "role": current_user.role
    }

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str = ""

# Only used for initial setup or testing. In production, only Admin can create users via /users Endpoint.
@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=UserRole.ADMIN # Default register is Admin for now (until we protect this endpoint)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "message": "Đăng ký thành công", "role": user.role}
