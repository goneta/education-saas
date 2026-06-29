import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import academics as academics_router
from backend.services import academics


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _setup(db):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"G {uid}", domain_prefix=f"g_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{uid}@g.local", hashed_password="x", full_name="A", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    su = models.User(email=f"s_{uid}@g.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add_all([admin, su]); db.flush()
    student = models.StudentProfile(user_id=su.id, registration_number=f"R{uid[:4]}")
    cls = models.Class(name="C1", level="6e", school_id=school.id)
    subj = models.Subject(name="Maths", school_id=school.id)
    term = models.Term(name="T1")
    db.add_all([student, cls, subj, term]); db.flush()
    db.commit()
    return school, admin, student, cls, subj, term


def _assessment(db, cls, subj, term, max_score, weight):
    a = models.Assessment(title="A", type=models.AssessmentType.EXAM, date=datetime(2026, 1, 1), max_score=max_score, weight=weight, class_id=cls.id, subject_id=subj.id, term_id=term.id)
    db.add(a); db.flush()
    return a


def test_weighted_gpa_computation():
    db = _session()
    school, admin, student, cls, subj, term = _setup(db)
    # 16/20 weight 1  and 12/20 weight 3 → weighted fraction = (0.8*1 + 0.6*3)/4 = 0.65
    a1 = _assessment(db, cls, subj, term, 20, 1)
    a2 = _assessment(db, cls, subj, term, 20, 3)
    db.add(models.Grade(score=16, assessment_id=a1.id, student_id=student.id))
    db.add(models.Grade(score=12, assessment_id=a2.id, student_id=student.id))
    db.commit()
    result = academics.compute_gpa(db, student.id)
    assert result["percentage"] == 65.0
    assert result["average_20"] == 13.0
    assert result["gpa_4"] == 2.6
    assert result["assessments_counted"] == 2


def test_term_scoped_gpa_and_endpoint_tenant_check():
    db = _session()
    school, admin, student, cls, subj, term = _setup(db)
    other_term = models.Term(name="T2"); db.add(other_term); db.flush()
    a1 = _assessment(db, cls, subj, term, 20, 1)
    a2 = _assessment(db, cls, subj, other_term, 20, 1)
    db.add(models.Grade(score=10, assessment_id=a1.id, student_id=student.id))
    db.add(models.Grade(score=20, assessment_id=a2.id, student_id=student.id))
    db.commit()
    # Term-scoped only sees a1 (10/20 → 50%).
    scoped = academics_router.student_gpa(student.id, term_id=term.id, db=db, current_user=admin)
    assert scoped["percentage"] == 50.0 and scoped["assessments_counted"] == 1
    # A different school's admin cannot read this student's GPA.
    uid = uuid.uuid4().hex[:6]
    other_school = models.School(name=f"O {uid}", domain_prefix=f"o_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(other_school); db.flush()
    other_admin = models.User(email=f"oa_{uid}@g.local", hashed_password="x", full_name="OA", role=models.UserRole.SCHOOL_ADMIN, school_id=other_school.id, is_active=True)
    db.add(other_admin); db.commit()
    try:
        academics_router.student_gpa(student.id, db=db, current_user=other_admin)
        assert False, "cross-school GPA read should be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404


def test_no_grades_returns_zero():
    db = _session()
    school, admin, student, cls, subj, term = _setup(db)
    result = academics.compute_gpa(db, student.id)
    assert result["percentage"] == 0.0 and result["assessments_counted"] == 0
