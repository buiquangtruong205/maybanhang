import sqlite3

DB_PATH = "database/app.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code INTEGER,
            amount INTEGER,
            status TEXT
        )
    """)
    db.commit()
    db.close()

def create_order(order_code, amount):
    db = get_db()
    db.execute(
        "INSERT INTO orders (order_code, amount, status) VALUES (?, ?, ?)",
        (order_code, amount, "PENDING")
    )
    db.commit()
    db.close()

def update_order_status(order_code, status):
    db = get_db()
    db.execute(
        "UPDATE orders SET status=? WHERE order_code=?",
        (status, order_code)
    )
    db.commit()
    db.close()

def get_orders():
    db = get_db()
    rows = db.execute("SELECT * FROM orders").fetchall()
    db.close()
    return rows
