from app import create_app, db
from app.models import DeviceLog

app = create_app()

with app.app_context():
    try:
        count = DeviceLog.query.count()
        print(f"\n📊 Total Device Logs in DB: {count}")
        
        if count > 0:
            latest = DeviceLog.query.order_by(DeviceLog.created_at.desc()).first()
            print(f"   Latest Log: [{latest.level}] {latest.message} at {latest.created_at}")
        else:
            print("   ⚠️  Table exists but IS EMPTY.")
            
    except Exception as e:
        print(f"\n❌ Error querying database: {e}")
        print("   This might mean the table 'device_logs' does not exist yet.")
