import asyncio
import sys
import os

# Thêm thư mục hiện tại vào path để import được app
sys.path.append(os.getcwd())

from app.db.database import engine, Base
from app.models.issue import Issue
from app.models.user import User
from app.models.machine import Machine

from sqlalchemy import text

async def create_tables():
    print("Đang xóa và khởi tạo lại bảng issues...")
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS issues"))
        await conn.run_sync(Base.metadata.create_all)
    print("Khởi tạo bảng thành công!")

if __name__ == "__main__":
    asyncio.run(create_tables())
