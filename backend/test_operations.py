import requests
import json

BASE_URL = "http://127.0.0.1:5001/api/v1"

def login(username, password):
    response = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    print(f"❌ Login failed: {response.text}")
    return None

def refill_slot(token, slot_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/slots/{slot_id}/refill", headers=headers)
    if response.status_code == 200:
        print(f"✅ Refilled slot {slot_id} successfully!")
        return True
    print(f"❌ Refill failed: {response.text}")
    return False

def report_issue(token, machine_id, content):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"machine_id": machine_id, "content": content}
    response = requests.post(f"{BASE_URL}/issues/", json=data, headers=headers)
    if response.status_code == 200:
        print(f"✅ Reported issue: '{content}'")
        return True
    print(f"❌ Report issue failed: {response.text}")
    return False

def create_staff_user():
    # Admin login to create user
    admin_token = login("admin", "admin123")
    if not admin_token: return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Check if staff exists
    response = requests.get(f"{BASE_URL}/users/", headers=headers)
    users = response.json()
    for u in users:
        if u['username'] == 'staff01':
            print("ℹ️ Staff user 'staff01' already exists.")
            return True
            
    # Create staff
    data = {"username": "staff01", "password": "password123", "full_name": "Nhân viên Kho", "role": "STAFF"}
    response = requests.post(f"{BASE_URL}/users/", json=data, headers=headers)
    if response.status_code == 200:
        print("✅ Created staff user 'staff01'")
        return True
    print(f"❌ Failed to create staff: {response.text}")
    return False

def main():
    print("🚀 Starting Operations Simulation...")
    
    # 1. Ensure Staff User Exists
    if not create_staff_user(): return

    # 2. Login as Staff
    print("\n🔐 Logging in as Staff...")
    token = login("staff01", "password123")
    if not token: return

    # 3. Simulate Refill
    print("\n📦 Simulating Refill...")
    
    # Login as Admin to empty the slot first
    admin_token = login("admin", "admin123")
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    slots = requests.get(f"{BASE_URL}/slots/", headers=headers_admin).json()
    
    if slots:
        slot_id = slots[0]['id']
        print(f"   ℹ️ Emptying slot {slot_id} (Current: {slots[0]['stock']}/{slots[0]['capacity']})...")
        requests.put(f"{BASE_URL}/slots/{slot_id}", json={"stock": 0}, headers=headers_admin)
        
        # Now refill as Staff
        print(f"   ℹ️ Staff refilling slot {slot_id}...")
        refill_slot(token, slot_id)
    else:
        print("⚠️ No slots found to refill.")

    # 4. Simulate Issue Report
    print("\n⚠️ Simulating Issue Report...")
    machines = requests.get(f"{BASE_URL}/machines/").json()
    if machines:
        machine_id = machines[0]['id']
        report_issue(token, machine_id, "Máy kêu to khi nhả hàng")
        report_issue(token, machine_id, "Hết tiền lẻ thối lại")
    else:
        print("⚠️ No machines found.")

if __name__ == "__main__":
    main()
