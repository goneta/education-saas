import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_system_config():
    # 1. Login as Admin (reuse logic)
    print("--- Authenticating ---")
    unique_id = str(uuid.uuid4())[:8]
    email = f"admin_{unique_id}@test.com"
    password = "securepassword123"
    
    # Register purely to get a valid token
    auth_payload = {
        "school": {
            "name": f"Config School {unique_id}",
            "domain_prefix": f"config_{unique_id}",
            "school_type": "general",
            "address": "123 Config St"
        },
        "owner": {
            "email": email,
            "full_name": "Config Admin",
            "role": "school_admin", # Authorized role
            "password": password
        }
    }
    requests.post(f"{BASE_URL}/auth/register/school", json=auth_payload)
    login_res = requests.post(f"{BASE_URL}/auth/token", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Token Acquired")

    # 2. Fetch Default Levels
    print("\n--- Testing Fetch Education Levels ---")
    res = requests.get(f"{BASE_URL}/system/reference-data/EDUCATION_LEVEL", headers=headers)
    if res.status_code == 200:
        levels = res.json()
        print(f"✅ Fetched {len(levels)} levels.")
        if len(levels) > 0:
            print(f"   Example: {levels[0]['key']} - {levels[0]['value']}")
    else:
        print(f"❌ Fetch Failed: {res.text}")

    # 3. Add Custom Level (Multilanguage)
    print("\n--- Testing Add Custom Level ---")
    custom_payload = {
        "category": "EDUCATION_LEVEL",
        "key": f"CUSTOM_{unique_id}",
        "value": {"fr": "Classe Spéciale", "en": "Special Class", "sw": "Darasa Maalum"},
        "order": 999
    }
    
    res = requests.post(f"{BASE_URL}/system/reference-data", json=custom_payload, headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Custom Level Added: {data['key']}")
        print(f"   Values: {data['value']}")
    else:
        print(f"❌ Add Level Failed: {res.text}")

if __name__ == "__main__":
    test_system_config()
