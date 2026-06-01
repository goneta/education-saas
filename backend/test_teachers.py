import pytest
from fastapi.testclient import TestClient
from backend.main import app
import uuid
import datetime

client = TestClient(app)

def test_teachers_flow():
    # 1. Setup: Register School & Admin
    unique_id = str(uuid.uuid4())[:8]
    domain = f"school_{unique_id}"
    admin_email = f"admin_{unique_id}@test.com"
    password = "SecurePass123!"

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
    
    # Register School
    res = client.post("/auth/register/school", json=auth_payload)
    assert res.status_code == 200 or res.status_code == 201
    
    # Login
    login_res = client.post("/auth/token", data={"username": admin_email, "password": password})
    assert login_res.status_code == 200
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Admin Logged In")

    # 2. Register Teacher
    print("\n--- Testing Teacher Registration ---")
    teacher_email = f"teacher_{unique_id}@test.com"
    teacher_payload = {
         "email": teacher_email,
         "password": "TeacherPass123!",
         "full_name": "Monsieur Prof",
         "role": "teacher",
         "profile": {
             "specialization": "Mathematics",
             "bio": "Experienced math teacher"
         }
    }
    
    res = client.post("/teachers/", json=teacher_payload, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: {res.text}")
    assert res.status_code == 200
    
    teacher_data = res.json()
    teacher_id = teacher_data['id']
    print(f"✅ Teacher Registered: {teacher_data['full_name']} (ID: {teacher_id})")

    # 3. Create Class and Assign Teacher
    print("\n--- Testing Class Assignment ---")
    class_payload = {"name": "6eme A", "level": "6eme", "main_teacher_id": teacher_id}
    res = client.post("/education/classes", json=class_payload, headers=headers)
    assert res.status_code == 200
    
    cls_data = res.json()
    class_id = cls_data['id']
    print(f"✅ Class Created with Teacher: {cls_data['name']} -> {cls_data['main_teacher_id']}")

    # 4. Create Subject
    print("\n--- Testing Subject Creation ---")
    subject_payload = {"name": "Maths", "code": "MATH"}
    res = client.post("/education/subjects", json=subject_payload, headers=headers)
    assert res.status_code == 200
    
    sub_data = res.json()
    subject_id = sub_data['id']
    print(f"✅ Subject Created: {sub_data['name']}")

    # 5. Create Timetable Entry with Teacher
    print("\n--- Testing Timetable Assignment ---")
    timetable_payload = {
        "day_of_week": "monday",
        "start_time": "08:00:00",
        "end_time": "10:00:00",
        "room": "101",
        "class_id": class_id,
        "subject_id": subject_id,
        "teacher_id": teacher_id
    }
    res = client.post("/education/timetables", json=timetable_payload, headers=headers)
    assert res.status_code == 200
    
    tt_data = res.json()
    print(f"✅ Timetable Entry Created with Teacher: {tt_data['teacher_id']}")

    # 6. Verify List
    print("\n--- Verify List Teachers ---")
    res = client.get("/teachers/", headers=headers)
    assert res.status_code == 200
    print(f"✅ Listed {len(res.json())} teachers")
    
    # 7. Delete Teacher
    print("\n--- Testing Delete Teacher ---")
    res = client.delete(f"/teachers/{teacher_id}", headers=headers)
    assert res.status_code == 204
    print("✅ Teacher Deleted")

if __name__ == "__main__":
    test_teachers_flow()
