import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from backend import database, models
from backend.main import app


client = TestClient(app)


def test_weak_password_is_rejected_on_school_registration():
    response = client.post("/auth/register/school", json={
        "school": {"name": "Weak Password School", "domain_prefix": f"weak_{uuid.uuid4().hex[:8]}", "school_type": "general", "address": "x"},
        "owner": {"email": f"weak_{uuid.uuid4().hex[:8]}@test.com", "full_name": "Admin", "role": "school_admin", "password": "password"},
    })
    assert response.status_code == 400


def test_failed_login_locks_account_and_records_event():
    password = "SecurePass123!"
    email = f"lock_{uuid.uuid4().hex[:8]}@test.com"
    client.post("/auth/register/school", json={
        "school": {"name": "Lock School", "domain_prefix": f"lock_{uuid.uuid4().hex[:8]}", "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })

    for _ in range(5):
        client.post("/auth/token", data={"username": email, "password": "WrongPass123!"})
    locked = client.post("/auth/token", data={"username": email, "password": password})
    assert locked.status_code == 423

    db = database.SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        events = db.query(models.SecurityEvent).filter(models.SecurityEvent.actor_id == user.id, models.SecurityEvent.event_type == "login_failed").count()
        assert events >= 5
    finally:
        db.close()


def test_security_headers_are_present():
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors" in response.headers["Content-Security-Policy"]


def test_document_verification_requires_reference_code():
    db = database.SessionLocal()
    try:
        school = models.School(name="Verify School", domain_prefix=f"verify_{uuid.uuid4().hex[:8]}", school_type="general")
        db.add(school)
        db.flush()
        student_user = models.User(
            email=f"verify_student_{uuid.uuid4().hex[:8]}@test.com",
            full_name="Verify Student",
            role=models.UserRole.STUDENT,
            hashed_password="unused",
            school_id=school.id,
        )
        db.add(student_user)
        db.flush()
        student_profile = models.StudentProfile(
            user_id=student_user.id,
            registration_number=f"VER-{uuid.uuid4().hex[:8]}",
            parent_name="Parent",
            parent_phone="+2250102030405",
        )
        db.add(student_profile)
        db.flush()
        fee = models.Fee(title="Inscription", amount=1000, due_date=datetime.utcnow(), school_id=school.id, student_id=student_profile.id)
        db.add(fee)
        db.flush()
        payment = models.Payment(amount=1000, fee_id=fee.id, receipt_number=f"RCPT-{uuid.uuid4().hex[:8]}")
        db.add(payment)
        db.commit()
        payment_id = payment.id
        receipt_number = payment.receipt_number
    finally:
        db.close()

    missing_code = client.get(f"/documents/verify/receipt/{payment_id}")
    assert missing_code.status_code == 404
    valid_code = client.get(f"/documents/verify/receipt/{payment_id}", params={"code": receipt_number})
    assert valid_code.status_code == 200
    assert valid_code.json()["valid"] is True
