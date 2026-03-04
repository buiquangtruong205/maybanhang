from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🔄 Attempting to add 'quantity' column to 'orders' table...")
    try:
        # Check if column exists first (optional but good)
        # Using raw SQL for Postgres
        db.session.execute(text("ALTER TABLE orders ADD COLUMN quantity INTEGER DEFAULT 1 NOT NULL"))
        db.session.commit()
        print("✅ Successfully added 'quantity' column.")
    except Exception as e:
        if "already exists" in str(e):
             print("ℹ️ Column 'quantity' already exists.")
        else:
             print(f"❌ Error adding column: {e}")
             # Print full traceback if needed
             import traceback
             traceback.print_exc()
