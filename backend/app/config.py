import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (find it in project root)
# Go up from app/config.py -> app -> backend -> project root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_HOURS = 24

# PayOS Configuration
PAYOS_CLIENT_ID = os.environ.get('PAYOS_CLIENT_ID', '')
PAYOS_API_KEY = os.environ.get('PAYOS_API_KEY', '')
PAYOS_CHECKSUM_KEY = os.environ.get('PAYOS_CHECKSUM_KEY', '')
DOMAIN = os.environ.get('DOMAIN', 'http://localhost:5000')

# Machine Keys for IoT device authentication
# Format: key -> machine_id mapping
MACHINE_KEYS = {
    'may1': 1,  # Key 'may1' corresponds to machine_id 1
    'may2': 2,  # Key 'may2' corresponds to machine_id 2
    # Add more keys as needed
}



# =============================================================================
# Application Security Configuration (L   ayer 3-4)
# =============================================================================
# Timestamp tolerance (seconds) - allow clock drift between ESP32 and server
TIMESTAMP_TOLERANCE_SECONDS = int(os.environ.get('TIMESTAMP_TOLERANCE', '30'))

# Nonce TTL (seconds) - how long to keep nonces to prevent replay
NONCE_TTL_SECONDS = int(os.environ.get('NONCE_TTL', '120'))

# =============================================================================
# Security Logging
# =============================================================================
IOT_SECURITY_LOG_LEVEL = os.environ.get('IOT_SECURITY_LOG_LEVEL', 'WARNING')