import uuid

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _school_admin(prefix: str):
    password = "SecurePass123!"
    email = f"admin_{prefix}_{uuid.uuid4().hex[:6]}@test.com"
    domain = f"{prefix}_{uuid.uuid4().hex[:8]}"
    school = client.post("/auth/register/school", json={
        "school": {"name": f"School {prefix}", "domain_prefix": domain, "school_type": "primary", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    }).json()
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return school, {"Authorization": f"Bearer {token}"}


def test_enrolled_admission_student_appears_in_roster():
    school, headers = _school_admin("roster")
    client.post(f"/system/schools/{school['id']}/apply-template", headers=headers, json={"template": "primary"})
    class_id = client.get("/education/classes", headers=headers).json()[0]["id"]
    admission = client.post("/operations/admissions", headers=headers, json={
        "applicant_name": "Future Student",
        "applicant_phone": "0101",
        "applicant_email": "parent@example.test",
        "desired_level": "CP1",
    }).json()

    enroll = client.post(f"/operations/admissions/{admission['id']}/enroll", headers=headers, json={
        "email": f"student_{uuid.uuid4().hex[:8]}@test.com",
        "full_name": "Future Student",
        "class_id": class_id,
    })
    assert enroll.status_code == 200, enroll.text
    student_user_id = enroll.json()["student_user_id"]

    # The enrolled student must be visible in the standard student roster, which
    # only lists students that have a StudentEnrollment.
    roster = client.get("/students", headers=headers)
    assert roster.status_code == 200
    assert any(row["id"] == student_user_id for row in roster.json())
