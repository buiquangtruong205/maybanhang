import asyncio
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def upgrade_user_table():
    async with AsyncSessionLocal() as db:
        print("Đang thêm cột email và is_active vào bảng users...")
        try:
            # Add email column
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;"))
            # Add is_active column
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
            
            await db.commit()
            print("✅ Đã cập nhật bảng users thành công!")
        except Exception as e:
            await db.rollback()
            print(f"❌ Lỗi cập nhật: {str(e)}")

if __name__ == "__main__":
    asyncio.run(upgrade_user_table())
