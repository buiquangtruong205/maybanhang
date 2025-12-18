"""
Order Model - Quản lý đơn hàng trong database SQLite
"""
import sqlite3
from config import DATABASE_PATH


def get_db():
    """Kết nối đến database"""
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    """Khởi tạo bảng orders nếu chưa tồn tại"""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code INTEGER UNIQUE,
            amount INTEGER,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    db.close()


def create_order(order_code: int, amount: int) -> None:
    """Tạo đơn hàng mới"""
    db = get_db()
    db.execute(
        "INSERT INTO orders (order_code, amount, status) VALUES (?, ?, ?)",
        (order_code, amount, "PENDING")
    )
    db.commit()
    db.close()


def update_order_status(order_code: int, status: str) -> None:
    """Cập nhật trạng thái đơn hàng"""
    db = get_db()
    db.execute(
        "UPDATE orders SET status=? WHERE order_code=?",
        (status, order_code)
    )
    db.commit()
    db.close()


def get_orders() -> list:
    """Lấy danh sách tất cả đơn hàng"""
    db = get_db()
    rows = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    db.close()
    return rows


def get_order_by_code(order_code: int):
    """Lấy thông tin đơn hàng theo mã"""
    db = get_db()
    row = db.execute(
        "SELECT * FROM orders WHERE order_code=?", 
        (order_code,)
    ).fetchone()
    db.close()
    return row
