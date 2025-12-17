import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
API_KEY = os.getenv("PAYOS_API_KEY")
CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
DOMAIN = os.getenv("DOMAIN")
