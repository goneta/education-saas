import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_flow():
    # Generate unique data to ensure clean test every time
    unique_id = str(uuid.uuid4())[:8]
    domain = f"school_{unique_id}"
    email = f"admin_{unique_id}@test.com"
    password = "SecurePass123!"

    # 1. Register School & Admin
    print(f"Testing Registration with domain={domain}...")
    payload = {
        "school": {
            "name": f"Test School {unique_id}",
            "domain_prefix": domain,
            "school_type": "general",
            "address": "123 Education St"
        },
        "owner": {
            "email": email,
            "full_name": "Test Admin",
            "role": "school_admin",
            "password": password
        }
    }
    
    try:
        res = requests.post(f"{BASE_URL}/auth/register/school", json=payload)
        if res.status_code == 200:
            print("✅ Registration Success:", res.json())
        elif res.status_code == 400:
            print("ℹ️ Registration Skipped (Likely already exists)")
        else:
            print("❌ Registration Failed:", res.text)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 2. Login
    print(f"\nTesting Login for {email}...")
    login_data = {
        "username": email,
        "password": password
    }
    
    try:
        res = requests.post(f"{BASE_URL}/auth/token", data=login_data)
        if res.status_code == 200:
            token = res.json()["access_token"]
            print("✅ Login Success! Token acquired.")
            
            # 3. Verify Token
            headers = {"Authorization": f"Bearer {token}"}
            me_res = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print("✅ Protected Route Data:", me_res.json())
        else:
            print("❌ Login Failed:", res.text)
    except Exception as e:
        print(f"❌ Login Connection Failed: {e}")

if __name__ == "__main__":
    test_flow()
