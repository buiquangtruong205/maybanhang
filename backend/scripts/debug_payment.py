import asyncio
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def debug_stock():
    async with AsyncSessionLocal() as db:
        # Check orders
        res_orders = await db.execute(text("SELECT order_code, status, product_id, machine_id FROM orders ORDER BY created_at DESC LIMIT 5"))
        orders = res_orders.all()
        print("\n--- Recent Orders ---")
        for o in orders:
            print(f"Code: {o[0]}, Status: {o[1]}, Product: {o[2]}, Machine: {o[3]}")
            
        # Check slots
        res_slots = await db.execute(text("SELECT slot_code, product_id, stock, machine_id FROM slots"))
        slots = res_slots.all()
        print("\n--- Current Slots ---")
        for s in slots:
            print(f"Slot: {s[0]}, Product: {s[1]}, Stock: {s[2]}, Machine: {s[3]}")

if __name__ == "__main__":
    asyncio.run(debug_stock())
