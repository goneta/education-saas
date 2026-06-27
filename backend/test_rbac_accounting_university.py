import uuid

from fastapi.testclient import TestClient

from backend import database, models, security
from backend.main import app


client = TestClient(app)


def _admin(prefix: str):
    password = "SecurePass123!"
    email = f"admin_{prefix}_{uuid.uuid4().hex[:6]}@test.com"
    domain = f"{prefix}_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register/school", json={
        "school": {"name": f"School {prefix}", "domain_prefix": domain, "school_type": "university", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email, password


def _create_user(email: str, role: models.UserRole, school_id: int, password: str = "SecurePass123!"):
    db = database.SessionLocal()
    try:
        user = models.User(
            email=email,
            hashed_password=security.get_password_hash(password),
            full_name=f"{role.value} User",
            role=role,
            school_id=school_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def _school_id(headers):
    return client.get("/auth/me", headers=headers).json()["school_id"]


def _student(headers):
    return client.post("/students/", headers=headers, json={
        "email": f"s_{uuid.uuid4().hex[:8]}@test.com",
        "password": "SecurePass123!",
        "full_name": "Student",
        "role": "student",
        "profile": {
            "registration_number": f"MAT{uuid.uuid4().hex[:8]}",
            "date_of_birth": "2010-01-01T00:00:00",
            "gender": "F",
            "parent_name": "Parent",
            "parent_phone": "+2250102030405",
        },
    }).json()


def test_school_admin_can_disable_cashier_write_permission():
    admin_headers, _, _ = _admin("rbac")
    school_id = _school_id(admin_headers)
    cashier_email = f"cashier_{uuid.uuid4().hex[:8]}@test.com"
    _create_user(cashier_email, models.UserRole.CASHIER, school_id)
    cashier_headers = {"Authorization": f"Bearer {client.post('/auth/token', data={'username': cashier_email, 'password': 'SecurePass123!'}).json()['access_token']}"}

    response = client.put("/system/role-permissions/cashier", headers=admin_headers, json={"permissions": ["finance:read", "reports:read"]})
    assert response.status_code == 200
    assert "finance:write" in response.json()["disabled_permissions"]

    denied = client.post("/finance/fees", headers=cashier_headers, json={"title": "Inscription", "amount": 1000})
    assert denied.status_code == 403


def test_payment_creates_balanced_journal_entry():
    headers, _, _ = _admin("acct")
    student = _student(headers)
    fee = client.post("/finance/fees", headers=headers, json={"title": "Inscription", "amount": 1000, "student_id": student["id"]}).json()

    paid = client.post(f"/finance/fees/{fee['id']}/payments", headers=headers, json={"amount": 1000}).json()
    assert paid["remaining_balance"] == 0

    journal = client.get("/enterprise/journal-entries", headers=headers).json()
    assert any(row["source_type"] == "payment" for row in journal)
    balance = client.get("/enterprise/trial-balance", headers=headers).json()
    assert balance["total_debit"] == balance["total_credit"] == 1000


def test_fee_with_timezone_aware_due_date_does_not_crash():
    """Regression test: a fee created with a timezone-aware ISO due_date (the
    format produced by JavaScript's Date.toISOString(), e.g. ending in "Z")
    must not raise a naive/aware datetime comparison error when the backend
    computes invoice status and overdue notifications."""
    headers, _, _ = _admin("tzfee")
    student = _student(headers)

    future_due = "2099-01-01T00:00:00Z"
    fee = client.post("/finance/fees", headers=headers, json={
        "title": "Tuition with aware due date",
        "amount": 500,
        "due_date": future_due,
        "student_id": student["id"],
    })
    assert fee.status_code == 200, fee.text
    assert fee.json()["status"] == "pending"

    past_due = "2000-01-01T00:00:00Z"
    overdue_fee = client.post("/finance/fees", headers=headers, json={
        "title": "Overdue tuition with aware due date",
        "amount": 300,
        "due_date": past_due,
        "student_id": student["id"],
    })
    assert overdue_fee.status_code == 200, overdue_fee.text

    paid = client.post(f"/finance/fees/{fee.json()['id']}/payments", headers=headers, json={"amount": 100})
    assert paid.status_code == 200, paid.text


def test_lmd_summary_computes_credits_and_gpa():
    headers, _, _ = _admin("lmd")
    student = _student(headers)
    semester = client.post("/enterprise/semesters", headers=headers, json={"name": "Semestre 1", "code": "S1"}).json()
    course = client.post("/enterprise/course-units", headers=headers, json={"code": "UE101", "name": "Methodologie", "credits": 6, "semester_id": semester["id"]}).json()

    enrollment = client.post("/enterprise/course-enrollments", headers=headers, json={
        "student_id": student["student_profile"]["id"],
        "course_unit_id": course["id"],
        "semester_id": semester["id"],
        "score": 15,
    })
    assert enrollment.status_code == 200

    summary = client.get(f"/enterprise/students/{student['student_profile']['id']}/lmd-summary", headers=headers).json()
    assert summary["credits_attempted"] == 6
    assert summary["credits_validated"] == 6
    assert summary["gpa"] == 3
