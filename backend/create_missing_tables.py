import asyncio
from app.db.database import engine, Base
import app.models # Ensure all models are imported

async def create_tables():
    print("Đang kiểm tra và tạo các bảng còn thiếu...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Hoàn tất việc tạo bảng!")

if __name__ == "__main__":
    asyncio.run(create_tables())
