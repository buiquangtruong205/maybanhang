#!/usr/bin/env python3
"""
Script test API nhanh
"""
import requests
import json

def test_products_api():
    """Test API products"""
    base_url = "http://172.16.1.217:5000"
    
    print("🧪 Testing Products API...")
    print("=" * 50)
    
    try:
        # Test GET /api/products
        print("\n1. GET /api/products")
        response = requests.get(f"{base_url}/api/products", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['success']}")
            print(f"📦 Products count: {len(data['data'])}")
            
            # Hiển thị 3 sản phẩm đầu
            for i, product in enumerate(data['data'][:3]):
                print(f"  {i+1}. {product['name']} - {product['price']:,}đ (Stock: {product['stock']})")
        else:
            print(f"❌ Error: {response.text}")
    
        # Test GET /api/products/1
        print("\n2. GET /api/products/1")
        response = requests.get(f"{base_url}/api/products/1", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            product = response.json()
            print(f"✅ Product: {product['name']} - {product['price']:,}đ")
            print(f"📝 Description: {product['description']}")
        else:
            print(f"❌ Error: {response.text}")
    
        # Test POST /api/create-payment
        print("\n3. POST /api/create-payment")
        payload = {
            "machine_id": "VM001",
            "product_id": 1,
            "amount": 15000
        }
        
        response = requests.post(f"{base_url}/api/create-payment", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payment created: Order {data['order_code']}")
            print(f"🔗 Checkout URL: {data.get('checkout_url', 'N/A')}")
            
            # Test order status
            order_code = data['order_code']
            print(f"\n4. GET /api/order-status/{order_code}")
            response = requests.get(f"{base_url}/api/order-status/{order_code}", timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"✅ Order status: {status_data.get('status', 'UNKNOWN')}")
            else:
                print(f"❌ Error: {response.text}")
        else:
            print(f"❌ Error: {response.text}")
            
        print("\n" + "=" * 50)
        print("✅ API Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_products_api()