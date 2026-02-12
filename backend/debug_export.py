import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.db.database import AsyncSessionLocal
from app.services.stats_service import StatsService

async def main():
    async with AsyncSessionLocal() as db:
        try:
            print("Starting export...")
            output = await StatsService.export_orders_excel(db)
            print("Export successful!")
            with open("test_export.xlsx", "wb") as f:
                f.write(output.read())
            print("File written.")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
