import asyncio
from app.db.database import AsyncSessionLocal
from app.services.log_service import LogService
import json

async def test_refill_logs():
    async with AsyncSessionLocal() as db:
        print("Đang truy vấn nhật ký nạp hàng...")
        try:
            logs = await LogService.get_refill_logs(db)
            print(f"✅ Thành công! Lấy được {len(logs)} bản ghi.")
            for log in logs:
                print(f"- Log ID: {log.id}, User: {log.user.username if log.user else 'N/A'}")
        except Exception as e:
            import traceback
            print("❌ Lỗi Backend:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_refill_logs())
