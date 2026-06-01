import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid
from backend.main import app

client = TestClient(app)

def test_attendance_flow():
    # 0. Setup: Register School & Admin to get valid credentials
    unique_id = str(uuid.uuid4())[:8]
    domain = f"school_{unique_id}"
    email = f"admin_{unique_id}@test.com"
    password = "securepassword123"
    
    # Register School
    school_payload = {
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
    
    reg_res = client.post("/auth/register/school", json=school_payload)
    if reg_res.status_code != 200:
        pytest.fail(f"Registration failed: {reg_res.text}")
        
    # Login
    login_res = client.post("/auth/token", data={
        "username": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Class
    class_res = client.post("/education/classes", json={
        "name": "Attendance Test Class",
        "level": "Test Level"
    }, headers=headers)
    assert class_res.status_code == 200
    class_id = class_res.json()["id"]
    
    # 2. Create Subject
    subject_res = client.post("/education/subjects", json={
        "name": "Attendance Test Subject"
    }, headers=headers)
    assert subject_res.status_code == 200
    subject_id = subject_res.json()["id"]
    
    # 3. Create Timetable Slot
    timetable_res = client.post("/education/timetables", json={
        "day_of_week": "monday",
        "start_time": "08:00:00",
        "end_time": "09:00:00",
        "class_id": class_id,
        "subject_id": subject_id
    }, headers=headers)
    assert timetable_res.status_code == 200
    timetable_id = timetable_res.json()["id"]
    
    # 4. Create Student
    student_email = f"att_st_{unique_id}@test.com"
    student_res = client.post("/students/", json={
        "email": student_email,
        "password": "password",
        "school_domain_prefix": domain, # Important: Join the same school
        "full_name": "Attendance Student",
        "role": "student",
        "profile": {
            "registration_number": f"ATT-{unique_id}",
            "date_of_birth": "2010-01-01T00:00:00",
            "gender": "M",
            "parent_name": "Parent",
            "parent_phone": "+2250102030405",
            "current_class_id": class_id
        }
    }, headers=headers)
    
    if student_res.status_code != 200:
        pytest.fail(f"Student creation failed: {student_res.text}")
        
    student_id = student_res.json()["id"]
        
    # 5. Mark Attendance (Batch)
    date_str = datetime.now().isoformat()
    response = client.post("/attendance/batch", json={
        "timetable_id": timetable_id,
        "date": date_str,
        "students": [
            {
                "student_id": student_id,
                "status": "present",
                "remarks": "On time"
            }
        ]
    }, headers=headers)
    
    if response.status_code != 200:
        pytest.fail(f"Batch attendance failed: {response.text}")
        
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "present"
    
    # 6. Get Attendance
    get_res = client.get(f"/attendance/?timetable_id={timetable_id}", headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1
    
    # 7. Get Stats
    stats_res = client.get(f"/attendance/stats?class_id={class_id}", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total"] >= 1
    assert stats["present"] >= 1
    
    print("Attendance Test Passed")

if __name__ == "__main__":
    test_attendance_flow()
