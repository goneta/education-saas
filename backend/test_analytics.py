import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import analytics


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"A {uid}", domain_prefix=f"an_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{uid}@an.local", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, admin


def _student(db, school, name):
    u = models.User(email=f"{name}_{uuid.uuid4().hex[:5]}@an.local", hashed_password="x", full_name=name, role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(u); db.flush()
    db.add(models.StudentProfile(user_id=u.id, registration_number=f"R{uuid.uuid4().hex[:4]}"))
    db.commit()


def test_csv_export_is_tenant_scoped():
    db = _session()
    school_a, admin_a = _school(db)
    school_b, admin_b = _school(db)
    _student(db, school_a, "Alice")
    _student(db, school_a, "Bob")
    _student(db, school_b, "Zoe")
    resp = analytics.export_csv("students", db=db, current_user=admin_a)
    assert resp.media_type == "text/csv"
    body = resp.body.decode() if isinstance(resp.body, bytes) else resp.body
    assert "full_name" in body and "Alice" in body and "Bob" in body
    assert "Zoe" not in body  # other school excluded
    # School B sees only its own.
    resp_b = analytics.export_csv("students", db=db, current_user=admin_b)
    assert "Zoe" in (resp_b.body.decode() if isinstance(resp_b.body, bytes) else resp_b.body)


def test_export_unknown_dataset_and_authz():
    db = _session()
    school, admin = _school(db)
    try:
        analytics.export_csv("nope", db=db, current_user=admin)
        assert False, "unknown dataset should 404"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404
    student = models.User(email=f"s_{uuid.uuid4().hex[:5]}@an.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student); db.commit()
    try:
        analytics.export_csv("students", db=db, current_user=student)
        assert False, "student cannot export"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def test_ai_insights_returns_kpis_and_text():
    db = _session()
    school, admin = _school(db)
    _student(db, school, "Cara")
    out = analytics.ai_insights(db=db, current_user=admin)
    assert out["kpis"]["students"] == 1
    assert out["insights"]  # local fallback still returns a message
