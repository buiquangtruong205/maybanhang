import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (find it in project root)
# Go up from app/config.py -> app -> backend -> project root -> infra
env_path = Path(__file__).resolve().parent.parent.parent / 'infra' / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_HOURS = 24
    MASTER_REGISTRATION_KEY = os.environ.get('MASTER_REGISTRATION_KEY', 'maybanhang-v3-factory')

# PayOS Configuration
PAYOS_CLIENT_ID = os.environ.get('PAYOS_CLIENT_ID', '')
PAYOS_API_KEY = os.environ.get('PAYOS_API_KEY', '')
PAYOS_CHECKSUM_KEY = os.environ.get('PAYOS_CHECKSUM_KEY', '')
DOMAIN = os.environ.get('DOMAIN', 'http://localhost:5000')

_PAYOS_PLACEHOLDERS = {
    '',
    'your_client_id',
    'your_client_id_here',
    'your_api_key',
    'your_api_key_here',
    'your_checksum_key',
    'your_checksum_key_here',
}


def _is_placeholder(value: str) -> bool:
    return (value or '').strip() in _PAYOS_PLACEHOLDERS


def validate_startup_config() -> None:
    invalid_vars = []

    if _is_placeholder(PAYOS_CLIENT_ID):
        invalid_vars.append('PAYOS_CLIENT_ID')
    if _is_placeholder(PAYOS_API_KEY):
        invalid_vars.append('PAYOS_API_KEY')
    if _is_placeholder(PAYOS_CHECKSUM_KEY):
        invalid_vars.append('PAYOS_CHECKSUM_KEY')

    if invalid_vars:
        joined = ', '.join(invalid_vars)
        raise RuntimeError(
            'Invalid PayOS configuration. '
            f'The following env vars are empty or still placeholders: {joined}. '
            'Update infra/.env with real PayOS credentials before starting backend.'
        )

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
