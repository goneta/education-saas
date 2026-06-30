import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import education


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_admin(db):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"R {uid}", domain_prefix=f"r_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{uid}@r.local", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, admin


def _enrol(db, school, cls, n, dob=datetime(2014, 5, 1), gender="M"):
    for i in range(n):
        u = models.User(email=f"s{i}_{uuid.uuid4().hex[:5]}@r.local", hashed_password="x", full_name=f"Eleve {i}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
        db.add(u); db.flush()
        db.add(models.StudentProfile(user_id=u.id, registration_number=f"R{uuid.uuid4().hex[:5]}", current_class_id=cls.id, date_of_birth=dob, gender=gender))
    db.commit()


def test_room_capacity_blocks_oversized_class():
    db = _session()
    school, _ = _school_admin(db)
    cls = models.Class(name="CP1 A", level="CP1", school_id=school.id); db.add(cls); db.flush()
    db.add(models.Room(school_id=school.id, name="Salle 1", capacity=25)); db.commit()
    _enrol(db, school, cls, 30)
    # 30 students into a 25-seat room -> blocked.
    try:
        education._room_capacity_check(db, school.id, cls.id, "Salle 1")
        assert False, "oversized class should be blocked"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409
    # A roomier room / unknown room / no capacity -> no-op.
    db.add(models.Room(school_id=school.id, name="Amphi", capacity=100)); db.commit()
    education._room_capacity_check(db, school.id, cls.id, "Amphi")
    education._room_capacity_check(db, school.id, cls.id, "Inexistante")
    education._room_capacity_check(db, school.id, cls.id, None)


def test_class_students_returns_age_and_sex():
    db = _session()
    school, admin = _school_admin(db)
    cls = models.Class(name="6e A", level="6EME", school_id=school.id); db.add(cls); db.flush()
    db.commit()
    _enrol(db, school, cls, 3, dob=datetime(2012, 1, 1), gender="F")
    out = education.class_students(cls.id, current_user=admin, db=db)
    assert out["count"] == 3
    assert all(s["gender"] == "F" and isinstance(s["age"], int) and s["age"] > 10 for s in out["students"])
    assert "full_name" in out["students"][0]
