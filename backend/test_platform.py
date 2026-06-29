import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import platform


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_user(db, role=models.UserRole.SCHOOL_ADMIN):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"Pl {uid}", domain_prefix=f"pl_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    user = models.User(email=f"a_{uid}@pl.local", hashed_password="x", full_name="Admin", role=role, school_id=school.id, is_active=True)
    db.add(user)
    db.commit()
    return school, user


def test_department_crud_and_tenant_scope():
    db = _session()
    school_a, admin_a = _school_user(db)
    school_b, admin_b = _school_user(db)
    dept = platform.create_department(schemas.DepartmentCreate(name="Sciences", code="SCI"), db=db, current_user=admin_a)
    assert dept.school_id == school_a.id
    assert len(platform.list_departments(db=db, current_user=admin_a)) == 1
    assert len(platform.list_departments(db=db, current_user=admin_b)) == 0  # isolation


def test_department_write_requires_admin():
    db = _session()
    school, _ = _school_user(db)
    student = models.User(email=f"s_{uuid.uuid4().hex[:6]}@pl.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student); db.commit()
    try:
        platform.create_department(schemas.DepartmentCreate(name="X"), db=db, current_user=student)
        assert False, "student must not create departments"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def test_feature_flag_override_falls_back_to_default():
    db = _session()
    school, admin = _school_user(db)
    # Platform default OFF.
    db.add(models.FeatureFlag(key="ai_tutor", school_id=None, is_enabled=False))
    db.commit()
    assert platform.feature_enabled(db, "ai_tutor", school.id) is False
    # School override ON wins over the default.
    platform.set_feature_flag(schemas.FeatureFlagSet(key="ai_tutor", is_enabled=True), db=db, current_user=admin)
    assert platform.feature_enabled(db, "ai_tutor", school.id) is True
    # Upsert: flipping again does not create a duplicate.
    platform.set_feature_flag(schemas.FeatureFlagSet(key="ai_tutor", is_enabled=False), db=db, current_user=admin)
    rows = db.query(models.FeatureFlag).filter(models.FeatureFlag.key == "ai_tutor", models.FeatureFlag.school_id == school.id).all()
    assert len(rows) == 1 and rows[0].is_enabled is False


def test_global_search_is_typed_and_tenant_scoped():
    db = _session()
    school_a, admin_a = _school_user(db)
    school_b, admin_b = _school_user(db)
    # A student in school A.
    su = models.User(email=f"alice_{uuid.uuid4().hex[:5]}@pl.local", hashed_password="x", full_name="Alice Martin", role=models.UserRole.STUDENT, school_id=school_a.id, is_active=True)
    db.add(su); db.flush()
    db.add(models.StudentProfile(user_id=su.id, registration_number="MAT-001"))
    # A class in school A and a fee.
    db.add(models.Class(name="Alpha Class", level="6e", school_id=school_a.id))
    db.add(models.Fee(title="Alpha Tuition", amount=1000, school_id=school_a.id, status=models.FeeStatus.PENDING))
    db.commit()

    out = platform.global_search(q="Alpha", db=db, current_user=admin_a)
    types = {r["type"] for r in out["results"]}
    assert "class" in types and "fee" in types
    # School B sees none of A's data.
    out_b = platform.global_search(q="Alpha", db=db, current_user=admin_b)
    assert out_b["count"] == 0
    # Search by student name.
    assert any(r["type"] == "student" and r["label"] == "Alice Martin" for r in platform.global_search(q="Alice", db=db, current_user=admin_a)["results"])


def test_global_search_ignores_short_queries():
    db = _session()
    school, admin = _school_user(db)
    assert platform.global_search(q="a", db=db, current_user=admin)["results"] == []
