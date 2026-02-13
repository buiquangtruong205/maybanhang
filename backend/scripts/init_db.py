import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.db.database import engine, Base, AsyncSessionLocal
    from app.models.product import Product
    from app.models.machine import Machine
    from app.models.slot import Slot
    from app.models.order import Order
    from app.models.user import User # New import for FK
    from app.models.issue import Issue
    from app.models.setting import SystemSetting # New import
    from app.services.setting_service import SettingService # New import
    from sqlalchemy import select
    from app.core.config import settings
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

async def init_db():
    print(f"⏳ Connecting to database: {settings.DATABASE_URL.split('@')[1]}") # Hide password
    try:
        async with engine.begin() as conn:
            print("⏳ Dropping tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("⏳ Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created!")
    except Exception as e:
        print(f"❌ DB Error: {e}")
        raise

async def seed_data():
    print("⏳ Seeding initial data...")
    try:
        async with AsyncSessionLocal() as session:
            # Check if products exist
            result = await session.execute(select(Product))
            if result.scalars().first():
                print("⚠️ Data already exists. Skipping seed.")
                return

            # 1. Create Products
            products = [
                Product(name="Coca Cola", price=10000, image_url="/images/coke.png", category="drink", description="Vi ngot truyen thong"),
                Product(name="Pepsi", price=10000, image_url="/images/pepsi.png", category="drink", description="Da khát tuc thi"),
                Product(name="7Up", price=10000, image_url="/images/7up.png", category="drink", description="Vi chanh tuoi mat"),
                Product(name="Fanta", price=10000, image_url="/images/fanta.png", category="drink", description="Huong cam tu nhien"),
                Product(name="Aquafina", price=5000, image_url="/images/water.png", category="water", description="Tinh khiết"),
                Product(name="Nutriboost", price=15000, image_url="/images/nutri.png", category="milk", description="Sua trai cay"),
            ]
            session.add_all(products)
            await session.commit()
            
            # Reload products to get IDs
            p_coke = (await session.execute(select(Product).where(Product.name == "Coca Cola"))).scalar_one()
            p_pepsi = (await session.execute(select(Product).where(Product.name == "Pepsi"))).scalar_one()

            # 2. Create Machine
            machine = Machine(name="VM001", location="Sảnh chính", secret_key="may1", status="online")
            session.add(machine)
            await session.commit()
            
            # Reload machine to get ID
            m_vm001 = (await session.execute(select(Machine).where(Machine.name == "VM001"))).scalar_one()

            # 3. Create Slots
            slots = [
                Slot(machine_id=m_vm001.id, slot_code="A1", product_id=p_coke.id, stock=10, capacity=10),
                Slot(machine_id=m_vm001.id, slot_code="A2", product_id=p_pepsi.id, stock=10, capacity=10),
                Slot(machine_id=m_vm001.id, slot_code="B1", product_id=p_coke.id, stock=5, capacity=10),
            ]
            session.add_all(slots)
            await session.commit()
            
            print("✅ Seed data inserted successfully!")
            print(f"   - {len(products)} Products")
            print(f"   - 1 Machine (VM001)")
            print(f"   - {len(slots)} Slots")

            # 4. Seed System Settings
            print("⏳ Seeding System Settings...")
            await SettingService.initialize_defaults(session)
            print("✅ System Settings initialized!")

    except Exception as e:
        print(f"❌ Seed Error: {e}")
        raise

async def main():
    try:
        await init_db()
        await seed_data()
    except Exception as e:
        print(f"❌ Main Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
