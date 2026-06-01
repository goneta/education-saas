import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _admin(prefix: str):
    password = "pass12345"
    email = f"admin_{prefix}_{uuid.uuid4().hex[:6]}@test.com"
    domain = f"{prefix}_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register/school", json={
        "school": {"name": f"School {prefix}", "domain_prefix": domain, "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _student(headers, prefix: str):
    return client.post("/students/", headers=headers, json={
        "email": f"s_{uuid.uuid4().hex[:8]}@test.com",
        "password": "pass12345",
        "full_name": f"{prefix} Student",
        "role": "student",
        "profile": {
            "registration_number": f"MAT{uuid.uuid4().hex[:8]}",
            "date_of_birth": "2010-01-01T00:00:00",
            "gender": "F",
            "parent_name": "Parent",
            "parent_phone": "0700",
        },
    }).json()


def test_students_are_isolated_by_school():
    a = _admin("tenant_a")
    b = _admin("tenant_b")
    student = _student(a, "Tenant A")
    assert client.get(f"/students/{student['id']}", headers=a).status_code == 200
    assert client.get(f"/students/{student['id']}", headers=b).status_code == 404


def test_finance_records_are_isolated_by_school():
    a = _admin("finance_a")
    b = _admin("finance_b")
    student = _student(a, "Finance A")
    fee = client.post("/finance/fees", headers=a, json={"title": "Inscription", "amount": 1000, "student_id": student["id"]}).json()
    assert any(row["id"] == fee["id"] for row in client.get("/finance/fees", headers=a).json())
    assert all(row["id"] != fee["id"] for row in client.get("/finance/fees", headers=b).json())
