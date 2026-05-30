
import requests
import uuid

BASE_URL = "http://localhost:8000"

def seed_admin():
    unique_id = str(uuid.uuid4())[:8]
    domain = f"school_{unique_id}" # or just 'demo' for simplicity?
    # I'll use 'demo' to make it predictable for browser
    domain = "demo_school" 
    admin_email = "admin@demo.com"
    password = "password123"

    print(f"--- Seeding Admin {admin_email} ---")
    
    # Try login first
    login_res = requests.post(f"{BASE_URL}/auth/token", data={"username": admin_email, "password": password})
    if login_res.status_code == 200:
        print("✅ Admin already exists.")
        return

    auth_payload = {
        "school": {
            "name": "Demo School",
            "domain_prefix": domain,
            "school_type": "general",
            "address": "123 Demo St"
        },
        "owner": {
            "email": admin_email,
            "full_name": "Demo Admin",
            "role": "school_admin",
            "password": password
        }
    }
    
    # Register
    res = requests.post(f"{BASE_URL}/auth/register/school", json=auth_payload)
    if res.status_code == 200:
        print("✅ Admin seeded successfully.")
    else:
        print(f"❌ Failed to seed: {res.text}")

if __name__ == "__main__":
    seed_admin()
