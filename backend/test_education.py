import requests
import json
import uuid
import datetime

BASE_URL = "http://localhost:8000"

def test_education_flow():
    # 1. Setup: Register School & Admin
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
    
    requests.post(f"{BASE_URL}/auth/register/school", json=auth_payload)
    login_res = requests.post(f"{BASE_URL}/auth/token", data={"username": admin_email, "password": password})
    
    if login_res.status_code != 200:
        print(f"❌ Login Failed: {login_res.text}")
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin Logged In")

    # 2. Create Class
    print("\n--- Testing Classes ---")
    class_payload = {"name": "6eme A", "level": "6eme"}
    res = requests.post(f"{BASE_URL}/education/classes", json=class_payload, headers=headers)
    if res.status_code == 200:
        cls_data = res.json()
        class_id = cls_data['id']
        print(f"✅ Class Created: {cls_data['name']} (ID: {class_id})")
    else:
        print(f"❌ Class Creation Failed: {res.text}")
        return

    # 3. Create Subject
    print("\n--- Testing Subjects ---")
    subject_payload = {"name": "Mathematics", "code": "MATH", "coefficient": 5}
    res = requests.post(f"{BASE_URL}/education/subjects", json=subject_payload, headers=headers)
    if res.status_code == 200:
        sub_data = res.json()
        subject_id = sub_data['id']
        print(f"✅ Subject Created: {sub_data['name']} (ID: {subject_id})")
    else:
        print(f"❌ Subject Creation Failed: {res.text}")
        return

    # 4. Create Timetable Entry
    print("\n--- Testing Timetables ---")
    timetable_payload = {
        "day_of_week": "monday",
        "start_time": "08:00:00",
        "end_time": "10:00:00",
        "room": "101",
        "class_id": class_id,
        "subject_id": subject_id
    }
    res = requests.post(f"{BASE_URL}/education/timetables", json=timetable_payload, headers=headers)
    if res.status_code == 200:
        tt_data = res.json()
        tt_id = tt_data['id']
        print(f"✅ Timetable Entry Created: {tt_data['day_of_week']} {tt_data['start_time']}")
    else:
        print(f"❌ Timetable Creation Failed: {res.text}")
        return

    # 5. List Timetables
    res = requests.get(f"{BASE_URL}/education/timetables?class_id={class_id}", headers=headers)
    if res.status_code == 200 and len(res.json()) > 0:
        print(f"✅ Timetables Listed: Found {len(res.json())} entries")
    else:
        print("❌ Listing Timetables Failed or Empty")

    # 6. Delete Timetable Entry
    print("\n--- Testing Delete Timetable ---")
    res = requests.delete(f"{BASE_URL}/education/timetables/{tt_id}", headers=headers)
    if res.status_code == 204:
        print("✅ Timetable Entry Deleted")
    else:
        print(f"❌ Delete Timetable Failed: {res.status_code}")

    # 7. Cleanup (Optional, verify delete Class/Subject)
    print("\n--- Testing Delete Class/Subject ---")
    requests.delete(f"{BASE_URL}/education/classes/{class_id}", headers=headers)
    requests.delete(f"{BASE_URL}/education/subjects/{subject_id}", headers=headers)
    print("✅ Cleanup Sent")

if __name__ == "__main__":
    test_education_flow()
