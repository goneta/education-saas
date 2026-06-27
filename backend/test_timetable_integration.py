from datetime import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import education


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _fixtures(db):
    school = models.School(name="Int", domain_prefix="int", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    admin = models.User(email="admin@int.local", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school=school, is_active=True)
    a = models.User(email="a@int.local", hashed_password="x", full_name="Prof A", role=models.UserRole.TEACHER, school=school, is_active=True)
    b = models.User(email="b@int.local", hashed_password="x", full_name="Prof B", role=models.UserRole.TEACHER, school=school, is_active=True)
    cls = models.Class(name="6A", level="6", school_id=school.id)
    subject = models.Subject(name="Maths", code="M", school_id=school.id)
    db.add_all([admin, a, b, cls, subject])
    db.flush()
    entry = models.Timetable(day_of_week=models.DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(10, 0), class_id=cls.id, subject_id=subject.id, teacher_id=a.id)
    db.add(entry)
    db.commit()
    return school, admin, a, b, entry


def test_teacher_load_reports_weekly_hours():
    db = _session()
    _school, admin, a, _b, _entry = _fixtures(db)
    result = education.teacher_load(current_user=admin, db=db, school_id=None)
    row = next(r for r in result["teacher_load"] if r["teacher_id"] == a.id)
    assert row["sessions"] == 1
    assert row["minutes"] == 120
    assert row["hours"] == 2.0


def test_apply_substitution_reassigns_and_notifies():
    db = _session()
    school, admin, _a, b, entry = _fixtures(db)
    updated = education.apply_substitution(
        payload=schemas.SubstitutionApply(timetable_id=entry.id, substitute_teacher_id=b.id),
        current_user=admin, db=db, school_id=None,
    )
    assert updated.teacher_id == b.id
    # The substitute teacher received a timetable notification.
    notifications = db.query(models.NotificationHistory).filter(
        models.NotificationHistory.recipient_user_id == b.id,
        models.NotificationHistory.event_type == "timetable.substituted",
    ).all()
    assert len(notifications) >= 1
