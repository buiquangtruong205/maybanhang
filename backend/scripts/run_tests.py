import sys
import os
import traceback

print("🔹 Script started", flush=True)

try:
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("🔹 Path added", flush=True)

    from fastapi.testclient import TestClient
    print("🔹 TestClient imported", flush=True)
    
    from app.main import app
    print("🔹 App imported", flush=True)
    
    from app.core.config import settings
    print("🔹 Settings imported", flush=True)

    client = TestClient(app)
    print("🔹 Client created", flush=True)
except Exception as e:
    print(f"❌ Setup Error: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

def run_tests():
    print("🚀 Starting integration tests...", flush=True)
    
    # 1. Test Root
    try:
        print("Testing GET / ...", end=" ", flush=True)
        response = client.get("/")
        print(f"Status: {response.status_code}", end=" ", flush=True)
        assert response.status_code == 200
        print("✅ OK", flush=True)
    except Exception as e:
        print(f"❌ FAIL: {e}", flush=True)
        traceback.print_exc()

    # 2. Test Products
    try:
        print("Testing GET /api/v1/products/ ...", end=" ", flush=True)
        response = client.get("/api/v1/products/")
        print(f"Status: {response.status_code}", end=" ", flush=True)
        assert response.status_code == 200
        data = response.json()
        print(f"Data len: {len(data)}", end=" ", flush=True)
        assert len(data) >= 6
        print(f"✅ OK", flush=True)
    except Exception as e:
        print(f"❌ FAIL: {e}", flush=True)
        # traceback.print_exc() # Too verbose

    # 3. Test Machines
    try:
        print("Testing GET /api/v1/machines/ ...", end=" ", flush=True)
        response = client.get("/api/v1/machines/")
        print(f"Status: {response.status_code}", end=" ", flush=True)
        assert response.status_code == 200
        data = response.json()
        print(f"Data len: {len(data)}", end=" ", flush=True)
        assert len(data) >= 1
        print(f"✅ OK", flush=True)
    except Exception as e:
        print(f"❌ FAIL: {e}", flush=True)

    print("\n🎉 All tests completed!", flush=True)

if __name__ == "__main__":
    run_tests()
