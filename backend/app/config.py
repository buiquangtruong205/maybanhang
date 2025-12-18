"""
Configuration - Đọc các biến môi trường từ .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory: config.py -> app -> backend -> vending-machine-project (project root)
# Path(__file__) = config.py
# .parent = app/
# .parent.parent = backend/
# .parent.parent.parent = vending-machine-project/ (PROJECT ROOT)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env file from project root or backend folder
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env")

# PayOS Configuration
CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
API_KEY = os.getenv("PAYOS_API_KEY")
CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")

# App Configuration
DOMAIN = os.getenv("DOMAIN", "http://localhost:5000")

# Database Configuration - Use absolute path to project root's database folder
DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "database" / "app.db"))

