import httpx
import time
import json
import asyncio

BASE_URL = "http://127.0.0.1:5001/api/v1"

async def test_create_payment_link():
    print(f"🚀 Testing PayOS Real Flow: Buy Product ID 1 (Price 10000)")
    
    # Endpoint is /payments/create
    # Payload matches CreatePaymentRequest
    payload = {
        "product_id": 1,
        "machine_id": 1
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"POST {BASE_URL}/payments/create with payload: {payload}")
            response = await client.post(f"{BASE_URL}/payments/create", json=payload)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("✅ PayOS Response:")
                print(json.dumps(data, indent=2))
                
                if "checkout_url" in data:
                    print(f"\n👉 Link thanh toán: {data['checkout_url']}")
                    print(f"👉 Quét QR Code để thanh toán thử (Real Money!)")
                else:
                    print("⚠️ Warning: No checkout_url found")
            else:
                print("❌ Failed:")
                print(response.text)
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_create_payment_link())
