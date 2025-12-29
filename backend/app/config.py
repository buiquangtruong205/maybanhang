import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (find it in project root)
# Go up from app/config.py -> app -> backend -> project root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///vending.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_HOURS = 24

# PayOS Configuration
PAYOS_CLIENT_ID = os.environ.get('PAYOS_CLIENT_ID', '')
PAYOS_API_KEY = os.environ.get('PAYOS_API_KEY', '')
PAYOS_CHECKSUM_KEY = os.environ.get('PAYOS_CHECKSUM_KEY', '')
DOMAIN = os.environ.get('DOMAIN', 'http://localhost:5000')