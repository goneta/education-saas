import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid
from backend.main import app

client = TestClient(app)

def test_grades_flow():
    # 0. Setup: Register School & Admin
    unique_id = str(uuid.uuid4())[:8]
    domain = f"school_gr_{unique_id}"
    email = f"admin_gr_{unique_id}@test.com"
    password = "SecurePass123!"
    
    # Register School
    school_payload = {
        "school": {
            "name": f"Test School Grades {unique_id}",
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
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Academic Year & Term
    year_res = client.post("/education/academic-years", json={
        "name": "2024-2025",
        "start_date": "2024-09-01T00:00:00",
        "end_date": "2025-06-30T00:00:00",
        "is_current": True
    }, headers=headers)
    if year_res.status_code != 200:
        print("Year creation failed:", year_res.text)
    assert year_res.status_code == 200
    year_id = year_res.json()["id"]
    
    term_res = client.post("/education/terms", json={
        "name": "Term 1",
        "start_date": "2024-09-01T00:00:00",
        "end_date": "2024-12-31T00:00:00",
        "academic_year_id": year_id
    }, headers=headers)
    if term_res.status_code != 200:
        print("Term creation failed:", term_res.text)
    assert term_res.status_code == 200
    term_id = term_res.json()["id"]
    
    # 2. Create Student & Class & Subject
    class_res = client.post("/education/classes", json={
        "name": "Grades Class",
        "level": "Test Level",
        "main_teacher_id": None
    }, headers=headers)
    class_id = class_res.json()["id"]
    
    subject_res = client.post("/education/subjects", json={
        "name": "Mathematics"
    }, headers=headers)
    subject_id = subject_res.json()["id"]
    
    student_res = client.post("/students/", json={
        "email": f"st_gr_{unique_id}@test.com",
        "password": "StudentPass123!",
        "school_domain_prefix": domain,
        "full_name": "Grades Student",
        "role": "student",
        "profile": {
            "registration_number": f"GR-{unique_id}",
            "date_of_birth": "2010-01-01T00:00:00",
            "gender": "M",
            "parent_name": "Parent",
            "parent_phone": "+2250102030405",
            "current_class_id": class_id
        }
    }, headers=headers)
    student_id = student_res.json()["id"]
    
    # 3. Create Assessment
    assess_res = client.post("/grades/assessments", json={
        "title": "Math Exam 1",
        "type": "exam",
        "date": datetime.now().isoformat(),
        "max_score": 20,
        "weight": 2,
        "class_id": class_id,
        "subject_id": subject_id,
        "term_id": term_id
    }, headers=headers)
    if assess_res.status_code != 200:
        print("Assessment creation failed:", assess_res.text)
    assert assess_res.status_code == 200
    assessment_id = assess_res.json()["id"]
    
    # 4. Enter Grades (Bulk)
    bulk_res = client.post("/grades/entry/bulk", json={
        "assessment_id": assessment_id,
        "grades": [
            {
                "student_id": student_id,
                "score": 15.5,
                "comment": "Good job",
                "assessment_id": assessment_id 
            }
        ]
    }, headers=headers)
    if bulk_res.status_code != 200:
        print("Bulk entry failed:", bulk_res.text)
    assert bulk_res.status_code == 200
    
    # 5. Get Report Card
    print(f"Checking report for student {student_id}")
    report_res = client.get(f"/grades/reports/student/{student_id}/term/{term_id}", headers=headers)
    if report_res.status_code != 200:
        print("Report failed:", report_res.text)
    assert report_res.status_code == 200
    report = report_res.json()
    
    print("Report Data:", report)
    
    assert report["student_id"] == student_id
    assert len(report["subjects"]) == 1
    # Check new schema structure
    assert report["subjects"][0]["subject_name"] == "Mathematics"
    assert report["subjects"][0]["average"] == 15.5 
    assert report["overall_average"] == 15.5
    
    print("Grades Test Passed")

if __name__ == "__main__":
    test_grades_flow()
