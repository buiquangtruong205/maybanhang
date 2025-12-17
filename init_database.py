#!/usr/bin/env python3
"""
Script khởi tạo database cho ứng dụng PayOS
"""
import sqlite3
import os
from models import init_db, create_order, get_orders

def setup_database():
    """Khởi tạo database và tạo dữ liệu mẫu"""
    
    print("🗄️ Đang khởi tạo database...")
    
    # Tạo thư mục database nếu chưa có
    os.makedirs("database", exist_ok=True)
    
    # Khởi tạo database và bảng
    init_db()
    print("✅ Đã tạo bảng 'orders'")
    
    # Tạo một số đơn hàng mẫu
    sample_orders = [
        (1234567890, 50000),
        (1234567891, 100000),
        (1234567892, 25000),
    ]
    
    for order_code, amount in sample_orders:
        try:
            create_order(order_code, amount)
            print(f"✅ Đã tạo đơn hàng mẫu: #{order_code} - {amount:,}đ")
        except Exception as e:
            print(f"⚠️ Đơn hàng #{order_code} đã tồn tại")
    
    # Hiển thị danh sách đơn hàng
    print("\n📋 Danh sách đơn hàng hiện tại:")
    orders = get_orders()
    if orders:
        print("ID | Order Code | Amount | Status")
        print("-" * 40)
        for order in orders:
            print(f"{order[0]:2} | {order[1]:10} | {order[2]:6,}đ | {order[3]}")
    else:
        print("Chưa có đơn hàng nào")
    
    print(f"\n🎯 Database đã sẵn sàng tại: database/app.db")

def check_database():
    """Kiểm tra kết nối database"""
    try:
        db = sqlite3.connect("database/app.db")
        cursor = db.cursor()
        
        # Kiểm tra bảng orders
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Bảng 'orders' đã tồn tại")
            
            # Đếm số đơn hàng
            cursor.execute("SELECT COUNT(*) FROM orders")
            count = cursor.fetchone()[0]
            print(f"📊 Có {count} đơn hàng trong database")
            
        else:
            print("❌ Bảng 'orders' chưa tồn tại")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script khởi tạo Database PayOS")
    print("=" * 40)
    
    # Kiểm tra database hiện tại
    print("1. Kiểm tra database hiện tại:")
    check_database()
    
    print("\n2. Khởi tạo database:")
    setup_database()
    
    print("\n3. Kiểm tra lại sau khi khởi tạo:")
    check_database()
    
    print("\n🎉 Hoàn thành! Bạn có thể chạy app.py ngay bây giờ.")