import asyncio
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def check_machines():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT id, name FROM machines"))
        machines = result.all()
        print(f"Machines found: {machines}")

if __name__ == "__main__":
    asyncio.run(check_machines())
