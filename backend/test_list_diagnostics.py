import uuid

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import students as students_router
from backend.routers import teachers as teachers_router


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _context(db):
    tag = uuid.uuid4().hex[:6]
    org = models.Organization(name=f"Org {tag}")
    db.add(org); db.flush()
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL, organization_id=org.id)
    db.add(school); db.flush()
    model = models.SchoolModel(name=f"M {tag}", code=f"m_{tag}")
    db.add(model); db.flush()
    sma = models.SchoolModelAssignment(school_id=school.id, school_model_id=model.id, is_active=True)
    db.add(sma); db.flush()
    admin = models.User(email=f"a_{tag}@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, sma, admin


def _student(db, school, sma_id=None):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id if school else None, is_active=True)
    db.add(user); db.flush()
    db.add(models.StudentProfile(user_id=user.id, registration_number=f"R{tag}", school_model_assignment_id=sma_id))
    db.commit()
    return user


def test_students_diagnostics_healthy_school():
    db = _session()
    school, sma, admin = _context(db)
    _student(db, school)
    _student(db, school, sma_id=sma.id)

    report = students_router.list_students_diagnostics(current_user=admin, db=db)
    assert report["active_context"]["school_id"] == school.id
    assert report["stages"]["student_profiles_total"] == 2
    assert report["stages"]["final_list_count"] == 2
    assert report["hints"] == []


def test_students_diagnostics_pinpoints_wrong_school():
    db = _session()
    school_a, _sma_a, admin_a = _context(db)
    school_b, _sma_b, _admin_b = _context(db)
    _student(db, school_b)  # student lives under ANOTHER school

    report = students_router.list_students_diagnostics(current_user=admin_a, db=db)
    assert report["stages"]["final_list_count"] == 0
    assert report["stages"]["user_school_matches_context"] == 0
    assert school_b.id in report["student_user_school_ids"]
    assert any("autre établissement" in hint for hint in report["hints"])


def test_students_diagnostics_pinpoints_missing_profiles():
    db = _session()
    school, _sma, admin = _context(db)
    # A student-role user WITHOUT a StudentProfile row (manual SQL import case).
    tag = uuid.uuid4().hex[:5]
    db.add(models.User(email=f"raw_{tag}@example.com", hashed_password="x", full_name="Raw", role=models.UserRole.STUDENT, school_id=school.id, is_active=True))
    db.commit()

    report = students_router.list_students_diagnostics(current_user=admin, db=db)
    assert report["stages"]["student_profiles_total"] == 0
    assert any("student_profiles" in hint for hint in report["hints"])


def test_teachers_diagnostics_and_rbac():
    db = _session()
    school, _sma, admin = _context(db)
    tag = uuid.uuid4().hex[:5]
    db.add(models.User(email=f"t_{tag}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school.id, is_active=True))
    db.commit()

    report = teachers_router.list_teachers_diagnostics(current_user=admin, db=db)
    assert report["stages"]["teaching_role_users_total"] == 1
    assert report["stages"]["final_list_count"] == 1
    assert report["hints"] == []

    teacher = db.query(models.User).filter(models.User.role == models.UserRole.TEACHER).first()
    try:
        students_router.list_students_diagnostics(current_user=teacher, db=db)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403
