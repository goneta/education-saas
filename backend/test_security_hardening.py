import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from backend import database, models
from backend.main import app


client = TestClient(app)


def _admin_headers():
    password = "SecurePass123!"
    email = f"prod_admin_{uuid.uuid4().hex[:8]}@test.com"
    response = client.post("/auth/register/school", json={
        "school": {"name": "Production School", "domain_prefix": f"prod_{uuid.uuid4().hex[:8]}", "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    assert response.status_code == 200
    token = client.post("/auth/token", data={"username": email, "password": password})
    assert token.status_code == 200
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


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


def test_secure_file_upload_requires_auth_and_validates_download():
    denied = client.post("/files/", files={"file": ("doc.pdf", b"%PDF-1.4\n", "application/pdf")})
    assert denied.status_code == 401

    headers = _admin_headers()
    uploaded = client.post(
        "/files/",
        headers=headers,
        files={"file": ("doc.pdf", b"%PDF-1.4\n% secure test\n", "application/pdf")},
        data={"entity_type": "student", "entity_id": "test"},
    )
    assert uploaded.status_code == 200
    payload = uploaded.json()
    assert payload["content_type"] == "application/pdf"
    assert payload["status"] == "active"

    listing = client.get("/files/", headers=headers)
    assert listing.status_code == 200
    assert any(row["id"] == payload["id"] for row in listing.json())

    download = client.get(f"/files/{payload['id']}/download", headers=headers)
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")

    signed = client.get(f"/files/{payload['id']}/signed-url", headers=headers)
    assert signed.status_code == 200
    assert signed.json()["signed_url"]


def test_compliance_export_and_metrics_are_available_to_admins():
    headers = _admin_headers()
    export = client.get("/system/compliance/data-export", headers=headers)
    assert export.status_code == 200
    assert "users" in export.json()["payload"]

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert "ready" in ready.json()

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "education_saas_uptime_seconds" in metrics.text


def test_compliance_consent_and_retention_registry():
    headers = _admin_headers()
    users = client.get("/system/users", headers=headers)
    assert users.status_code == 200
    user_id = users.json()[0]["id"]

    consent = client.post("/system/compliance/consents", headers=headers, json={
        "subject_user_id": user_id,
        "consent_type": "communications",
        "granted": True,
        "source": "admin",
        "locale": "fr",
        "policy_version": "2026-06",
    })
    assert consent.status_code == 200
    assert consent.json()["consent_type"] == "communications"

    rule = client.post("/system/compliance/retention-rules", headers=headers, json={
        "data_category": "student_records",
        "retention_days": 3650,
        "legal_basis": "school administration",
        "action": "review",
    })
    assert rule.status_code == 200


def test_csv_student_import_creates_students():
    headers = _admin_headers()
    suffix = uuid.uuid4().hex[:8]
    csv_body = f"email,full_name,registration_number,parent_name,parent_phone\nimported_{suffix}@test.com,Imported Student,IMP-{suffix},Parent,+2250102030405\n"
    response = client.post(
        "/operations/imports/students",
        headers=headers,
        files={"file": ("students.csv", csv_body.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["created"] == 1
