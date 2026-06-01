import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _school_admin(prefix: str, school_type: str = "primary"):
    password = "pass12345"
    email = f"admin_{prefix}_{uuid.uuid4().hex[:6]}@test.com"
    domain = f"{prefix}_{uuid.uuid4().hex[:8]}"
    school = client.post("/auth/register/school", json={
        "school": {"name": f"School {prefix}", "domain_prefix": domain, "school_type": school_type, "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    }).json()
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return school, {"Authorization": f"Bearer {token}"}


def test_school_template_creates_default_structure():
    school, headers = _school_admin("template", "primary")

    result = client.post(f"/system/schools/{school['id']}/apply-template", headers=headers, json={"template": "primary"})

    assert result.status_code == 200
    payload = result.json()
    assert payload["created"]["classes"] >= 1
    assert payload["created"]["subjects"] >= 1
    assert payload["created"]["fees"] >= 1
    assert client.get("/education/classes", headers=headers).json()
    assert client.get("/finance/fee-schedules", headers=headers).json()


def test_admission_enrollment_creates_student_documents_and_fees():
    school, headers = _school_admin("enroll", "primary")
    client.post(f"/system/schools/{school['id']}/apply-template", headers=headers, json={"template": "primary"})
    class_id = client.get("/education/classes", headers=headers).json()[0]["id"]
    admission = client.post("/operations/admissions", headers=headers, json={
        "applicant_name": "Future Student",
        "applicant_phone": "0101",
        "applicant_email": "parent@example.test",
        "desired_level": "CP1",
    }).json()

    response = client.post(f"/operations/admissions/{admission['id']}/enroll", headers=headers, json={
        "email": f"student_{uuid.uuid4().hex[:8]}@test.com",
        "full_name": "Future Student",
        "class_id": class_id,
    })

    assert response.status_code == 200
    payload = response.json()
    assert payload["student_profile_id"]
    assert payload["class_id"] == class_id
    assert payload["generated_fees"] >= 1
    assert payload["registration_documents"] == 3
    fees = client.get(f"/finance/fees?student_id={payload['student_user_id']}", headers=headers).json()
    assert fees
