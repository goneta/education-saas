import requests
import json
import uuid
import datetime

BASE_URL = "http://localhost:8000"

def test_student_flow():
    # 1. Setup: Register School & Admin to get token
    unique_id = str(uuid.uuid4())[:8]
    domain = f"school_{unique_id}"
    admin_email = f"admin_{unique_id}@test.com"
    password = "securepassword123"

    print(f"--- Setup: Creating School {domain} ---")
    auth_payload = {
        "school": {
            "name": f"Test School {unique_id}",
            "domain_prefix": domain,
            "school_type": "general",
            "address": "123 Education St"
        },
        "owner": {
            "email": admin_email,
            "full_name": "Test Admin",
            "role": "school_admin",
            "password": password
        }
    }
    
    # Register/Login Logic (simplified from test_auth)
    requests.post(f"{BASE_URL}/auth/register/school", json=auth_payload)
    login_res = requests.post(f"{BASE_URL}/auth/token", data={"username": admin_email, "password": password})
    
    if login_res.status_code != 200:
        print(f"❌ Login Failed: {login_res.text}")
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin Logged In")

    # 2. Register Student
    print("\n--- Testing Student Registration ---")
    student_email = f"student_{unique_id}@test.com"
    matricule = f"MAT-{unique_id}"
    
    student_payload = {
        "email": student_email,
        "password": "studentpass123", # Students might default to matricule
        "full_name": "Jean Eleve",
        "role": "student",
        "school_domain_prefix": domain,
        "profile": {
            "registration_number": matricule,
            "date_of_birth": datetime.datetime(2010, 5, 15).isoformat(),
            "gender": "M",
            "student_address": "456 Student Lane",
            "parent_name": "Papa Eleve",
            "parent_phone": "+225 07070707",
            "parent_email": f"parent_{unique_id}@test.com",
            "parent_address": "789 Parent Blvd" # Testing new field
        }
    }

    try:
        res = requests.post(f"{BASE_URL}/students/", json=student_payload, headers=headers)
        if res.status_code == 200:
            data = res.json()
            print("✅ Student Registered Successfully")
            print(f"   ID: {data['id']}")
            print(f"   Name: {data['full_name']}")
            print(f"   Matricule: {data['student_profile']['registration_number']}")
            print(f"   Student Address: {data['student_profile']['student_address']}")
            print(f"   Parent Address: {data['student_profile']['parent_address']}")
        else:
            print(f"❌ Student Registration Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

    # 3. List Students
    print("\n--- Testing List Students ---")
    try:
        res = requests.get(f"{BASE_URL}/students/", headers=headers)
        if res.status_code == 200:
            students = res.json()
            print(f"✅ Retrieved {len(students)} students")
            if len(students) > 0:
                print(f"   First Student: {students[0]['full_name']}")
        else:
            print(f"❌ List Students Failed: {res.text}")
    except Exception as e:
        print(f"❌ List Connection Failed: {e}")

if __name__ == "__main__":
    test_student_flow()
