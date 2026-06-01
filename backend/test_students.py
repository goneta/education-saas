import datetime
import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _admin():
    unique_id = uuid.uuid4().hex[:8]
    domain = f"school_{unique_id}"
    email = f"admin_{unique_id}@test.com"
    password = "securepassword123"
    client.post("/auth/register/school", json={
        "school": {"name": f"Test School {unique_id}", "domain_prefix": domain, "school_type": "general", "address": "123 Education St"},
        "owner": {"email": email, "full_name": "Test Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, domain, unique_id


def test_student_flow():
    headers, domain, unique_id = _admin()
    matricule = f"MAT-{unique_id}"

    student_payload = {
        "email": f"student_{unique_id}@test.com",
        "password": "studentpass123",
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
            "parent_address": "789 Parent Blvd",
        },
    }

    created = client.post("/students/", json=student_payload, headers=headers)
    assert created.status_code == 200
    data = created.json()
    assert data["student_profile"]["registration_number"] == matricule

    listed = client.get("/students/", headers=headers)
    assert listed.status_code == 200
    assert any(student["id"] == data["id"] for student in listed.json())

    updated = client.put(f"/students/{data['id']}", json={"full_name": "Jean Eleve Updated", "profile": {"student_address": "Updated Address 123"}}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Jean Eleve Updated"
    assert updated.json()["student_profile"]["student_address"] == "Updated Address 123"

    deleted = client.delete(f"/students/{data['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/students/{data['id']}", headers=headers).status_code == 404
