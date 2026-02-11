import asyncio
import sys
import os

print("🚀 Starting test script...")

try:
    import asyncpg
    print("✅ asyncpg imported")
except ImportError as e:
    print(f"❌ ImportError: {e}")

async def main():
    print("⏳ Connecting to DB (127.0.0.1)...")
    try:
        # Use credentials from docker-compose.yml: user_iot / password123
        conn = await asyncpg.connect(user='user_iot', password='password123',
                                   database='vending_machine', host='127.0.0.1', port=5432)
        print("✅ DB Connected successfully!")
        
        # Test query
        version = await conn.fetchval('SELECT version()')
        print(f"📊 DB Version: {version}")
        
        await conn.close()
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
