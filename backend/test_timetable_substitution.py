from datetime import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import timetable_substitution


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _fixtures(db):
    school = models.School(name="Sub", domain_prefix="sub", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    cls = models.Class(name="6A", level="6", school_id=school.id)
    subject = models.Subject(name="Maths", code="M", school_id=school.id)
    db.add_all([cls, subject])
    db.flush()
    absent = models.User(email="absent@sub.local", hashed_password="x", full_name="Absent", role=models.UserRole.TEACHER, school=school, is_active=True)
    free = models.User(email="free@sub.local", hashed_password="x", full_name="Free", role=models.UserRole.TEACHER, school=school, is_active=True)
    busy = models.User(email="busy@sub.local", hashed_password="x", full_name="Busy", role=models.UserRole.TEACHER, school=school, is_active=True)
    db.add_all([absent, free, busy])
    db.flush()
    # Absent teacher gives a Monday 8-9 course.
    db.add(models.Timetable(day_of_week=models.DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(9, 0), class_id=cls.id, subject_id=subject.id, teacher_id=absent.id))
    # Busy teacher already teaches Monday 8-9 elsewhere.
    db.add(models.Timetable(day_of_week=models.DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(9, 0), class_id=cls.id, subject_id=subject.id, teacher_id=busy.id))
    db.commit()
    return school, absent, free, busy


def test_substitution_proposes_only_free_teachers():
    db = _session()
    school, absent, free, busy = _fixtures(db)
    proposals = timetable_substitution.propose_substitutions(db, school.id, absent.id, "monday")
    assert len(proposals) == 1
    sub_ids = {s["teacher_id"] for s in proposals[0]["substitutes"]}
    assert free.id in sub_ids       # free at that slot
    assert busy.id not in sub_ids   # already booked
    assert absent.id not in sub_ids  # cannot substitute themselves


def test_substitution_respects_availability_rule():
    db = _session()
    school, absent, free, _busy = _fixtures(db)
    # The only free teacher is restricted to Tuesday -> not eligible on Monday.
    db.add(models.TimetableConstraintRule(
        school_id=school.id, rule_type="teacher_available_days",
        parameters={"teacher_id": free.id, "days": ["tuesday"]}, is_active=True,
    ))
    db.commit()
    proposals = timetable_substitution.propose_substitutions(db, school.id, absent.id, "monday")
    assert all(free.id != s["teacher_id"] for s in proposals[0]["substitutes"])


def test_no_proposals_when_teacher_has_no_courses_that_day():
    db = _session()
    school, absent, _free, _busy = _fixtures(db)
    assert timetable_substitution.propose_substitutions(db, school.id, absent.id, "friday") == []
