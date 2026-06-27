import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _admin(prefix: str):
    uid = uuid.uuid4().hex[:8]
    email = f"admin_{prefix}_{uid}@test.com"
    password = "SecurePass123!"
    client.post("/auth/register/school", json={
        "school": {"name": f"S {prefix}", "domain_prefix": f"{prefix}_{uid}", "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    headers = {"Authorization": f"Bearer {client.post('/auth/token', data={'username': email, 'password': password}).json()['access_token']}"}
    client.post("/education/academic-years", json={"name": "2024-2025", "start_date": "2024-09-01T00:00:00", "end_date": "2025-06-30T00:00:00", "is_current": True}, headers=headers)
    class_id = client.post("/education/classes", json={"name": "6A", "level": "6", "main_teacher_id": None}, headers=headers).json()["id"]
    subject_id = client.post("/education/subjects", json={"name": "Physique"}, headers=headers).json()["id"]
    return headers, class_id, subject_id


def test_constraint_rule_crud_and_validation_integration():
    headers, class_id, subject_id = _admin("ttc")

    # Unsupported rule type is rejected.
    bad = client.post("/education/timetables/constraint-rules", headers=headers, json={"rule_type": "nonsense", "parameters": {}})
    assert bad.status_code == 400

    # Create a configurable rule: this subject must not be scheduled after 16:00.
    created = client.post("/education/timetables/constraint-rules", headers=headers, json={
        "rule_type": "subject_time_window",
        "name": "Sciences pas apres 16h",
        "parameters": {"subject_id": subject_id, "not_after": "16:00"},
        "severity": "blocking",
    })
    assert created.status_code == 200, created.text
    rule_id = created.json()["id"]
    assert any(r["id"] == rule_id for r in client.get("/education/timetables/constraint-rules", headers=headers).json())

    # Validation now reports the configured rule for a late slot.
    late = client.post("/education/timetables/validate", headers=headers, json={
        "day_of_week": "monday", "start_time": "16:00:00", "end_time": "17:00:00",
        "class_id": class_id, "subject_id": subject_id,
    })
    assert late.status_code == 200, late.text
    assert late.json()["has_conflicts"] is True
    assert any(c.get("rule_id") == rule_id for c in late.json()["conflicts"])

    # A compliant slot passes.
    early = client.post("/education/timetables/validate", headers=headers, json={
        "day_of_week": "monday", "start_time": "14:00:00", "end_time": "15:00:00",
        "class_id": class_id, "subject_id": subject_id,
    })
    assert early.status_code == 200
    assert all(c.get("rule_id") != rule_id for c in early.json()["conflicts"])

    # Deleting the rule clears the violation.
    assert client.delete(f"/education/timetables/constraint-rules/{rule_id}", headers=headers).status_code == 204
    again = client.post("/education/timetables/validate", headers=headers, json={
        "day_of_week": "monday", "start_time": "16:00:00", "end_time": "17:00:00",
        "class_id": class_id, "subject_id": subject_id,
    })
    assert all(c.get("rule_id") != rule_id for c in again.json()["conflicts"])


def test_constraint_rules_isolated_by_school():
    # Session-level (no HTTP) to keep the suite's auth-request volume low; the
    # tenant scoping lives in the router helpers exercised here directly.
    import pytest
    from fastapi import HTTPException
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from backend import database, models, schemas
    from backend.routers import education

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()

    def _school_admin(prefix):
        school = models.School(name=prefix, domain_prefix=prefix, school_type=models.SchoolType.GENERAL)
        db.add(school)
        db.flush()
        admin = models.User(email=f"{prefix}@t.local", hashed_password="x", full_name="A", role=models.UserRole.SCHOOL_ADMIN, school=school, is_active=True)
        db.add(admin)
        db.flush()
        return school, admin

    _school_a, admin_a = _school_admin("ttiso_a")
    _school_b, admin_b = _school_admin("ttiso_b")
    created = education.create_constraint_rule(
        payload=schemas.TimetableConstraintRuleCreate(rule_type="subject_max_per_day", parameters={"subject_id": 1, "max": 1}),
        current_user=admin_a, db=db, school_id=None,
    )

    # School B does not see school A's rule and cannot delete it.
    b_rules = education.list_constraint_rules(current_user=admin_b, db=db, school_id=None)
    assert all(r.id != created.id for r in b_rules)
    with pytest.raises(HTTPException) as exc:
        education.delete_constraint_rule(rule_id=created.id, current_user=admin_b, db=db, school_id=None)
    assert exc.value.status_code == 404
