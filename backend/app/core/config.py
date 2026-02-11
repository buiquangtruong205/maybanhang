from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PAYOS_CLIENT_ID: str
    PAYOS_API_KEY: str
    PAYOS_CHECKSUM_KEY: str
    
    PORT: int = 5000
    DOMAIN: str = "http://localhost:5000"
    
    # Updated to use port 5433
    DATABASE_URL: str = "postgresql+asyncpg://user_iot:password123@127.0.0.1:5433/vending_machine"
    
    SECRET_KEY: str = "your_secret_key_here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    MACHINE_KEYS: str = "may1,may2,may3"
    
    API_PRODUCTS: str = "http://localhost:5000/api/v1/products"
    API_MACHINES: str = "http://localhost:5000/api/v1/machines"
    API_PAYMENTS: str = "http://localhost:5000/api/v1/payments"
    API_SLOTS: str = "http://localhost:5000/api/v1/slots"

    class Config:
        env_file = ".env"

settings = Settings()
