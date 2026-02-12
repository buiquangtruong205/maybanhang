from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.core.security import get_password_hash

class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str):
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def create_user(db: AsyncSession, user_data: dict):
        if "password" in user_data:
            user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        
        new_user = User(**user_data)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, update_data: dict):
        user = await UserService.get_user_by_id(db, user_id)
        if user:
            if "password" in update_data and update_data["password"]:
                user.hashed_password = get_password_hash(update_data.pop("password"))
            
            for key, value in update_data.items():
                setattr(user, key, value)
            
            await db.commit()
            await db.refresh(user)
            return user
        return None

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int):
        user = await UserService.get_user_by_id(db, user_id)
        if user:
            await db.delete(user)
            await db.commit()
            return True
        return False
