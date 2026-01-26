import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_logs():
    print("1. Testing POST /api/iot/logs...")
    try:
        # 1. Post a log
        payload = {
            "level": "info",
            "message": "TEST_LOG_MESSAGE_123",
            "data": {"test": True}
        }
        headers = {"X-Machine-Key": "may1"}
        
        res = requests.post(f"{BASE_URL}/iot/logs", json=payload, headers=headers)
        print(f"   Status: {res.status_code}")
        print(f"   Response: {res.text}")
        
        if res.status_code != 201:
            print("❌ Failed to post log")
            return

        # 2. Login as admin to get token
        print("\n2. Logging in as admin...")
        res = requests.post(f"{BASE_URL}/login", json={"username": "admin", "password": "adminpassword"}) # Assuming default credentials or similar if created
        # If login fails (user doesn't exist), we can't test GET.
        # But wait, earlier we saw users table might be empty or specific password needed.
        # Let's try to register if login fails?
        
        if res.status_code != 200:
            print(f"   Login failed ({res.status_code}). Trying to register admin...")
            res = requests.post(f"{BASE_URL}/register", json={"username": "admin", "password": "adminpassword"})
            if res.status_code == 200:
                print("   Registered successfully. Logging in...")
                res = requests.post(f"{BASE_URL}/login", json={"username": "admin", "password": "adminpassword"})
            else:
                 print(f"   Register failed: {res.text}")
                 # Try to force create user via script if this fails?
                 
        if res.status_code == 200:
            token = res.json()['data']['access_token']
            print("   Login successful.")
            
            # 3. Get logs
            print("\n3. Testing GET /api/devices/logs...")
            res = requests.get(f"{BASE_URL}/devices/logs", headers={"Authorization": f"Bearer {token}"})
            print(f"   Status: {res.status_code}")
            data = res.json()
            # print(f"   Data: {json.dumps(data, indent=2)}")
            
            logs = data.get('data', [])
            found = any(l['message'] == "TEST_LOG_MESSAGE_123" for l in logs)
            
            if found:
                print("\n✅ SUCCESS: Log found in database!")
            else:
                print("\n❌ FAILED: Log POSTed but not found in GET response.")
                print(f"   Total logs returned: {len(logs)}")
        else:
            print("❌ Could not log in to check results.")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_logs()
