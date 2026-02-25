import asyncio
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def upgrade_db():
    async with AsyncSessionLocal() as db:
        print("Đang nâng cấp cột order_code lên BIGINT...")
        try:
            await db.execute(text("ALTER TABLE orders ALTER COLUMN order_code TYPE BIGINT;"))
            await db.commit()
            print("✅ Đã nâng cấp thành công!")
        except Exception as e:
            print(f"❌ Lỗi nâng cấp: {str(e)}")
            print("Có thể cột đã là BIGINT hoặc bảng chưa tồn tại.")

if __name__ == "__main__":
    asyncio.run(upgrade_db())
