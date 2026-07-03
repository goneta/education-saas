"""Regression tests for the production "empty lists" bug: /students and
/teachers returned 200 [] because the queries required an enrollment /
assignment row matching the exact active context — students and teachers
without one (legacy data, imports, pre-lifecycle records, NULL model
assignments) silently disappeared. The lists are now tolerant on read."""

import uuid
from datetime import datetime

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
    org = models.Organization(name="Org", is_active=True)
    db.add(org); db.flush()
    school = models.School(name="Sch", domain_prefix=f"s{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL, organization_id=org.id, is_active=True)
    db.add(school); db.flush()
    sm = models.SchoolModel(code=f"m{uuid.uuid4().hex[:4]}", name="Mod", is_active=True)
    db.add(sm); db.flush()
    assign = models.SchoolModelAssignment(school_id=school.id, school_model_id=sm.id, is_active=True)
    db.add(assign); db.flush()
    year = models.AcademicYear(name="2026-2027", school_id=school.id, school_model_assignment_id=assign.id, is_current=True)
    db.add(year); db.flush()
    admin = models.User(email=f"admin_{uuid.uuid4().hex[:6]}@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SUPER_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.flush()
    db.add(models.UserPreference(user_id=admin.id, active_organization_id=org.id, active_school_id=school.id, active_school_model_assignment_id=assign.id, active_academic_year_id=year.id))
    db.commit()
    return org, school, assign, year, admin


def _student(db, school, tag, sma_id=None):
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}", school_model_assignment_id=sma_id)
    db.add(profile); db.flush()
    return user, profile


def test_legacy_student_without_enrollment_is_visible():
    db = _session()
    org, school, assign, year, admin = _context(db)
    # Legacy student: profile only, no StudentGlobalProfile / StudentEnrollment.
    user, _profile = _student(db, school, uuid.uuid4().hex[:6])
    db.commit()
    rows = students_router.list_students(skip=0, limit=100, class_id=None, school_id=None, search=None, current_user=admin, db=db)
    assert any(r.id == user.id for r in rows), "legacy student must not disappear from the list"


def test_enrolled_student_still_visible_and_other_school_hidden():
    db = _session()
    org, school, assign, year, admin = _context(db)
    tag = uuid.uuid4().hex[:6]
    user, profile = _student(db, school, tag, sma_id=assign.id)
    gp = models.StudentGlobalProfile(student_profile_id=profile.id, user_id=user.id, global_student_number=f"G{tag}", first_name="S", last_name=tag)
    db.add(gp); db.flush()
    db.add(models.StudentEnrollment(
        student_global_profile_id=gp.id, organization_id=org.id, school_id=school.id,
        school_model_assignment_id=assign.id, academic_year_id=year.id,
        enrollment_status="active", start_date=datetime(2026, 9, 1),
    ))
    # A student that belongs to a different school must stay hidden.
    other = models.School(name="Other", domain_prefix=f"o{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL, organization_id=org.id, is_active=True)
    db.add(other); db.flush()
    outsider, _ = _student(db, other, uuid.uuid4().hex[:6])
    db.commit()

    rows = students_router.list_students(skip=0, limit=100, class_id=None, school_id=None, search=None, current_user=admin, db=db)
    ids = {r.id for r in rows}
    assert user.id in ids and outsider.id not in ids


def test_legacy_teacher_without_assignment_is_visible():
    db = _session()
    org, school, assign, year, admin = _context(db)
    teacher = models.User(email=f"t_{uuid.uuid4().hex[:6]}@example.com", hashed_password="x", full_name="Legacy Teacher", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.commit()
    rows = teachers_router.list_teachers(skip=0, limit=100, school_id=None, current_user=admin, db=db)
    assert any(r.id == teacher.id for r in rows), "legacy teacher must not disappear from the list"


def test_assignment_with_null_model_and_cross_school_teacher():
    db = _session()
    org, school, assign, year, admin = _context(db)
    # (a) Assignment predating the model-assignment concept (NULL sma) -> visible.
    t1 = models.User(email=f"t1_{uuid.uuid4().hex[:6]}@example.com", hashed_password="x", full_name="T1", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(t1); db.flush()
    db.add(models.TeacherAssignment(user_id=t1.id, school_id=school.id, school_model_assignment_id=None, is_active=True))
    # (b) Cross-school teacher: home school elsewhere, active assignment here -> visible.
    other = models.School(name="Other2", domain_prefix=f"o{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL, organization_id=org.id, is_active=True)
    db.add(other); db.flush()
    t2 = models.User(email=f"t2_{uuid.uuid4().hex[:6]}@example.com", hashed_password="x", full_name="T2", role=models.UserRole.TEACHER, school_id=other.id, is_active=True)
    db.add(t2); db.flush()
    db.add(models.TeacherAssignment(user_id=t2.id, school_id=school.id, school_model_assignment_id=assign.id, is_active=True))
    # (c) Teacher of the other school with no assignment here -> hidden.
    t3 = models.User(email=f"t3_{uuid.uuid4().hex[:6]}@example.com", hashed_password="x", full_name="T3", role=models.UserRole.TEACHER, school_id=other.id, is_active=True)
    db.add(t3); db.commit()

    rows = teachers_router.list_teachers(skip=0, limit=100, school_id=None, current_user=admin, db=db)
    ids = {r.id for r in rows}
    assert t1.id in ids and t2.id in ids and t3.id not in ids
