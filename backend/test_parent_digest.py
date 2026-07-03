import uuid
from datetime import datetime, time, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations
from backend.services import parent_digest


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_admin(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{tag}@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, admin


def _family(db, school, lang=None):
    tag = uuid.uuid4().hex[:5]
    student = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student); db.flush()
    profile = models.StudentProfile(user_id=student.id, registration_number=f"R{tag}")
    db.add(profile); db.flush()
    parent = models.User(email=f"par_{tag}@example.com", hashed_password="x", full_name=f"Parent {tag}", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.flush()
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=profile.id, is_active=True))
    if lang:
        db.add(models.UserPreference(user_id=parent.id, language=lang))
    db.commit()
    return profile, parent


def _grade(db, school, profile, score, max_score=20, days_ago=1):
    tag = uuid.uuid4().hex[:4]
    year = db.query(models.AcademicYear).filter(models.AcademicYear.school_id == school.id).first()
    if not year:
        year = models.AcademicYear(name="2026", school_id=school.id, start_date=datetime.utcnow() - timedelta(days=200), end_date=datetime.utcnow() + timedelta(days=100), is_current=True)
        db.add(year); db.flush()
    term = db.query(models.Term).filter(models.Term.academic_year_id == year.id).first()
    if not term:
        term = models.Term(name="T1", academic_year_id=year.id, start_date=year.start_date, end_date=year.end_date)
        db.add(term); db.flush()
    cls = models.Class(name=f"C{tag}", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"Sub{tag}", school_id=school.id)
    db.add(subject); db.flush()
    assessment = models.Assessment(title=f"A{tag}", date=datetime.utcnow() - timedelta(days=days_ago), max_score=max_score, class_id=cls.id, subject_id=subject.id, term_id=term.id)
    db.add(assessment); db.flush()
    db.add(models.Grade(score=score, assessment_id=assessment.id, student_id=profile.id))
    db.commit()


def _absence(db, school, profile, status, days_ago=1):
    tag = uuid.uuid4().hex[:4]
    cls = models.Class(name=f"CA{tag}", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"SubA{tag}", school_id=school.id)
    db.add(subject); db.flush()
    timetable = models.Timetable(class_id=cls.id, subject_id=subject.id, day_of_week=models.DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(9, 0))
    db.add(timetable); db.flush()
    db.add(models.Attendance(date=datetime.utcnow() - timedelta(days=days_ago), status=status, student_id=profile.id, timetable_id=timetable.id))
    db.commit()


def _pending_fee(db, school, profile, amount=25000):
    fee = models.Fee(title=f"F {uuid.uuid4().hex[:4]}", amount=amount, due_date=datetime.utcnow() + timedelta(days=10), status=models.FeeStatus.PENDING, student_id=profile.id, school_id=school.id)
    db.add(fee); db.commit()
    return fee


def test_digest_compiles_grades_absences_fees():
    db = _session()
    school, admin = _school_admin(db)
    profile, parent = _family(db, school)
    _grade(db, school, profile, score=15)
    _absence(db, school, profile, models.AttendanceStatus.ABSENT)
    _pending_fee(db, school, profile)

    summary = parent_digest.run_parent_digest(db, school.id, admin)
    db.commit()

    assert summary == {"links": 1, "digests": 1, "grade_alerts": 0, "absence_alerts": 0, "skipped_cooldown": 0}
    digest = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "parent.digest").one()
    assert digest.recipient_user_id == parent.id and digest.student_id == profile.id
    assert "15.0/20" in digest.message and "25,000" in digest.message


def test_threshold_alerts_fire():
    db = _session()
    school, admin = _school_admin(db)
    profile, _parent = _family(db, school)
    _grade(db, school, profile, score=6)          # avg 6/20 < 10 threshold
    for _ in range(3):
        _absence(db, school, profile, models.AttendanceStatus.ABSENT)

    summary = parent_digest.run_parent_digest(db, school.id, admin)
    db.commit()

    assert summary["digests"] == 1 and summary["grade_alerts"] == 1 and summary["absence_alerts"] == 1
    events = {n.event_type for n in db.query(models.NotificationHistory).all()}
    assert {"parent.digest", "parent.alert.average", "parent.alert.absences"} <= events


def test_rerun_is_idempotent_within_window():
    db = _session()
    school, admin = _school_admin(db)
    _family(db, school)

    first = parent_digest.run_parent_digest(db, school.id, admin)
    db.commit()
    second = parent_digest.run_parent_digest(db, school.id, admin)
    db.commit()

    assert first["digests"] == 1
    assert second["digests"] == 0 and second["skipped_cooldown"] == 1
    assert db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "parent.digest").count() == 1


def test_digest_uses_parent_language():
    db = _session()
    school, admin = _school_admin(db)
    _family(db, school, lang="en")
    _family(db, school, lang="sw")

    parent_digest.run_parent_digest(db, school.id, admin)
    db.commit()

    subjects = [n.subject for n in db.query(models.NotificationHistory).all()]
    assert any(s and s.startswith("Weekly digest") for s in subjects)
    assert any(s and s.startswith("Muhtasari wa wiki") for s in subjects)


def test_tenant_scope_and_endpoint_rbac():
    db = _session()
    school_a, admin_a = _school_admin(db)
    school_b, _admin_b = _school_admin(db)
    _family(db, school_b)

    summary = parent_digest.run_parent_digest(db, school_a.id, admin_a)
    db.commit()
    assert summary["links"] == 0 and summary["digests"] == 0

    teacher = models.User(email=f"t_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school_a.id, is_active=True)
    db.add(teacher); db.commit()
    try:
        automations.run_parent_digest(days=7, grade_alert_threshold=10.0, absence_alert_count=3, school_id=None, db=db, current_user=teacher)
        assert False
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403

    rows = automations.parent_digest_history(limit=50, school_id=None, db=db, current_user=admin_a)
    assert rows == []
