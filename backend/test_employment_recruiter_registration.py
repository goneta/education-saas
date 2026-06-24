import uuid

from fastapi.testclient import TestClient

from backend import database, models
from backend.main import app


client = TestClient(app)


def _payload(prefix: str) -> dict:
    return {
        "email": f"recruiter_{prefix}@test.com",
        "password": "SecurePass123!",
        "company_name": f"Recruiter Company {prefix}",
        "contact_name": f"Recruiter Contact {prefix}",
        "sector": "Technologie",
        "phone": "+2250707070707",
        "website": "https://example.com",
        "plan": "job_posts",
        "payment_provider": "manual",
    }


def test_recruiter_registration_creates_profile_payment_and_login_session():
    payload = _payload(uuid.uuid4().hex[:8])

    response = client.post("/employment/recruiters/register", json=payload)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["payment_status"] == "pending"
    assert body["user_id"]
    assert body["recruiter_id"]

    db = database.SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == payload["email"]).one()
        recruiter = db.query(models.RecruiterProfile).filter(models.RecruiterProfile.user_id == user.id).one()
        payment = db.query(models.PlatformPayment).filter(models.PlatformPayment.payer_user_id == user.id).one()
        assert recruiter.company_name == payload["company_name"]
        assert recruiter.payment_status == "pending"
        assert payment.payment_type == "employment_recruiter_subscription"
        assert payment.status == "pending"
    finally:
        db.close()

    token_response = client.post("/auth/token", data={"username": payload["email"], "password": payload["password"]})
    assert token_response.status_code == 200, token_response.text
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token_response.json()['access_token']}"})
    assert me.status_code == 200, me.text
    assert me.json()["account_type"] == "recruiter"
    assert me.json()["dashboard_path"] == "/dashboard/emploi-recruteur"
    assert me.json()["recruiter_payment_status"] == "pending"


def test_recruiter_registration_accepts_multiple_valid_datasets():
    first = _payload(uuid.uuid4().hex[:8])
    second = _payload(uuid.uuid4().hex[:8])
    second["plan"] = "cvtheque_limited"
    second["payment_provider"] = "free"

    first_response = client.post("/employment/recruiters/register", json=first)
    second_response = client.post("/employment/recruiters/register", json=second)

    assert first_response.status_code == 200, first_response.text
    assert second_response.status_code == 200, second_response.text
    assert first_response.json()["payment_status"] == "pending"
    assert second_response.json()["payment_status"] == "confirmed"
