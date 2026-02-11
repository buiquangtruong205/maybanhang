import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vending Machine API v2 is running"
    # Check if DB host is correct (should be hidden in prod but visible in dev)
    assert "127.0.0.1" in data["db"] or "localhost" in data["db"]

def test_get_products():
    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 6  # We seeded 6 products
    
    # Check specific product
    coke = next((p for p in data if p["name"] == "Coca Cola"), None)
    assert coke is not None
    assert coke["price"] == 10000

def test_get_machines():
    response = client.get("/api/v1/machines/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    machine = data[0]
    assert machine["name"] == "VM001"
    assert machine["status"] == "online"

def test_create_payment_link_mock():
    # Helper to mock PayOS response if needed, but here we test the flow
    # This might fail if PayOS credentials are fake, so we expect 400 or 500 or handling
    # But since we use real credentials (from .env), let's see.
    # Actually, verify that endpoint exists first.
    
    payment_payload = {
        "orderCode": 123456,
        "amount": 10000,
        "description": "Test Order",
        "items": [
            {"name": "Test Product", "quantity": 1, "price": 10000}
        ],
        "returnUrl": "/success",
        "cancelUrl": "/cancel"
    }
    
    # We won't actually call PayOS in this test to avoid spamming real API 
    # unless we want to. For now, just check if endpoint accepts request.
    # But authentication might be required or mocked.
    pass

def test_db_connection_settings():
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert "127.0.0.1:5433" in settings.DATABASE_URL # Port 5433 check
