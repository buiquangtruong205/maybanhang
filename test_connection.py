#!/usr/bin/env python3
"""
Script test kết nối database và PayOS API
"""
import sqlite3
from models import get_db, get_orders, create_order, update_order_status
from config import CLIENT_ID, API_KEY, CHECKSUM_KEY, DOMAIN
from payment_service import create_payment
import time

def test_database_connection():
    """Test kết nối SQLite database"""
    print("🗄️ Testing Database Connection...")
    
    try:
        # Test kết nối
        db = get_db()
        cursor = db.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        print(f"✅ Database connected successfully!")
        print(f"📊 Total orders: {count}")
        
        # Hiển thị 5 đơn hàng gần nhất
        cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
        recent_orders = cursor.fetchall()
        
        print("\n📋 5 đơn hàng gần nhất:")
        print("ID | Order Code | Amount | Status")
        print("-" * 40)
        for order in recent_orders:
            print(f"{order[0]:2} | {order[1]:10} | {order[2]:6,}đ | {order[3]}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_config():
    """Test cấu hình từ .env"""
    print("\n⚙️ Testing Configuration...")
    
    configs = {
        "CLIENT_ID": CLIENT_ID,
        "API_KEY": API_KEY, 
        "CHECKSUM_KEY": CHECKSUM_KEY,
        "DOMAIN": DOMAIN
    }
    
    for key, value in configs.items():
        if value:
            print(f"✅ {key}: {value[:20]}..." if len(str(value)) > 20 else f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: Not found")
    
    return all(configs.values())

def test_models():
    """Test các function trong models.py"""
    print("\n🔧 Testing Models Functions...")
    
    try:
        # Test tạo đơn hàng
        test_order_code = int(time.time())
        test_amount = 99000
        
        print(f"Creating test order: #{test_order_code}")
        create_order(test_order_code, test_amount)
        print("✅ create_order() works")
        
        # Test lấy danh sách đơn hàng
        orders = get_orders()
        print(f"✅ get_orders() works - Found {len(orders)} orders")
        
        # Test cập nhật trạng thái
        update_order_status(test_order_code, "PAID")
        print("✅ update_order_status() works")
        
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False

def test_payos_api():
    """Test PayOS API (sẽ fail nhưng kiểm tra kết nối)"""
    print("\n💳 Testing PayOS API...")
    
    try:
        test_order_code = int(time.time())
        test_amount = 50000
        
        print(f"Testing PayOS with order #{test_order_code}")
        result = create_payment(test_order_code, test_amount)
        
        if result and "code" in result:
            if result["code"] == "00":
                print("✅ PayOS API works perfectly!")
            else:
                print(f"⚠️ PayOS API responded with code: {result['code']}")
                print(f"   Message: {result.get('desc', 'Unknown error')}")
        else:
            print("❌ PayOS API returned unexpected response")
            
        return True
        
    except Exception as e:
        print(f"❌ PayOS API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing All Connections")
    print("=" * 50)
    
    # Test từng component
    db_ok = test_database_connection()
    config_ok = test_config()
    models_ok = test_models()
    payos_ok = test_payos_api()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"Database: {'✅ OK' if db_ok else '❌ FAIL'}")
    print(f"Config: {'✅ OK' if config_ok else '❌ FAIL'}")
    print(f"Models: {'✅ OK' if models_ok else '❌ FAIL'}")
    print(f"PayOS API: {'⚠️ CHECK' if payos_ok else '❌ FAIL'}")
    
    if db_ok and config_ok and models_ok:
        print("\n🎉 Ready to run: python app.py")
    else:
        print("\n🔧 Please fix the issues above before running app.py")