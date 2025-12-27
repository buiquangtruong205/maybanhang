"""
Cấu hình ứng dụng - đọc biến môi trường từ file .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm file .env - thử nhiều vị trí
possible_paths = [
    Path(__file__).parent.parent.parent / ".env",  # vending-machine-project/.env
    Path(__file__).parent.parent / ".env",          # payment_service/.env
    Path.cwd() / ".env",                            # current working directory
    Path.cwd().parent / ".env",                     # parent of cwd
]

for env_path in possible_paths:
    if env_path.exists():
        print(f"✅ Đã tìm thấy .env tại: {env_path}")
        load_dotenv(dotenv_path=env_path)
        break
else:
    print("⚠️ Không tìm thấy file .env, sử dụng biến môi trường hệ thống")
    load_dotenv()

# PayOS Credentials
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")

# Kiểm tra credentials
if not all([PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY]):
    print("❌ CẢNH BÁO: Thiếu PayOS credentials trong .env!")
    print(f"   CLIENT_ID: {'có' if PAYOS_CLIENT_ID else 'thiếu'}")
    print(f"   API_KEY: {'có' if PAYOS_API_KEY else 'thiếu'}")
    print(f"   CHECKSUM_KEY: {'có' if PAYOS_CHECKSUM_KEY else 'thiếu'}")

# Server Configuration
PORT = int(os.getenv("PORT", 3000))
DOMAIN = os.getenv("DOMAIN", f"http://localhost:{PORT}")
