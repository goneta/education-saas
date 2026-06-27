import uuid

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _admin(prefix: str):
    password = "SecurePass123!"
    email = f"admin_{prefix}_{uuid.uuid4().hex[:6]}@test.com"
    domain = f"{prefix}_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register/school", json={
        "school": {"name": f"School {prefix}", "domain_prefix": domain, "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _student(headers):
    return client.post("/students/", headers=headers, json={
        "email": f"s_{uuid.uuid4().hex[:8]}@test.com",
        "password": "SecurePass123!",
        "full_name": "Report Student",
        "role": "student",
        "profile": {
            "registration_number": f"MAT{uuid.uuid4().hex[:8]}",
            "date_of_birth": "2010-01-01T00:00:00",
            "gender": "F",
            "parent_name": "Parent",
            "parent_phone": "+2250102030405",
        },
    }).json()


def test_finance_reports_can_be_scoped_by_academic_year():
    admin = _admin("reports_year")
    student = _student(admin)
    fee = client.post("/finance/fees", headers=admin, json={"title": "Inscription", "amount": 1000, "student_id": student["id"]}).json()
    year_id = fee.get("academic_year_id")

    # Default (no context filter): the fee is part of the report.
    default_report = client.get("/finance/reports", headers=admin).json()
    assert default_report["total_expected"] >= 1000

    if year_id:
        # Matching academic year keeps the fee.
        same_year = client.get(f"/finance/reports?academic_year_id={year_id}", headers=admin).json()
        assert same_year["total_expected"] >= 1000
        # A different academic year excludes it.
        other_year = client.get(f"/finance/reports?academic_year_id={year_id + 100000}", headers=admin).json()
        assert other_year["total_expected"] == 0
        assert other_year["debtors"] == []


def test_finance_reports_scope_via_context_headers():
    # The frontend injects X-Academic-Year-ID globally; reports must honour it.
    admin = _admin("reports_hdr")
    student = _student(admin)
    fee = client.post("/finance/fees", headers=admin, json={"title": "Inscription", "amount": 1500, "student_id": student["id"]}).json()
    year_id = fee.get("academic_year_id")
    if year_id:
        matching = client.get("/finance/reports", headers={**admin, "X-Academic-Year-ID": str(year_id)}).json()
        assert matching["total_expected"] >= 1500
        other = client.get("/finance/reports", headers={**admin, "X-Academic-Year-ID": str(year_id + 100000)}).json()
        assert other["total_expected"] == 0


def test_finance_reports_can_be_scoped_by_model_assignment():
    admin = _admin("reports_model")
    student = _student(admin)
    fee = client.post("/finance/fees", headers=admin, json={"title": "Scolarite", "amount": 2000, "student_id": student["id"]}).json()
    assignment_id = fee.get("school_model_assignment_id")

    if assignment_id:
        same_model = client.get(f"/finance/reports?school_model_assignment_id={assignment_id}", headers=admin).json()
        assert same_model["total_expected"] >= 2000
        other_model = client.get(f"/finance/reports?school_model_assignment_id={assignment_id + 100000}", headers=admin).json()
        assert other_model["total_expected"] == 0
