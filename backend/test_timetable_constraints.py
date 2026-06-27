from datetime import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import timetable_constraints


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _fixtures(db):
    school = models.School(name="TT", domain_prefix="tt", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    cls = models.Class(name="6A", level="6", school_id=school.id)
    science = models.Subject(name="Physique", code="PHY", school_id=school.id, coefficient=4)
    sport = models.Subject(name="Sport", code="SPT", school_id=school.id, coefficient=1)
    teacher = models.User(email="t@tt.local", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school=school, is_active=True)
    db.add_all([cls, science, sport, teacher])
    db.flush()
    return school, cls, science, sport, teacher


def _candidate(cls, subject, *, day, start, end, teacher_id=None, room=None):
    return models.Timetable(
        day_of_week=day, start_time=start, end_time=end, room=room,
        class_id=cls.id, subject_id=subject.id, teacher_id=teacher_id,
    )


def _add_rule(db, school, rule_type, params, severity="warning"):
    rule = models.TimetableConstraintRule(school_id=school.id, rule_type=rule_type, parameters=params, severity=severity, is_active=True)
    db.add(rule)
    db.flush()
    return rule


def test_subject_time_window_rule():
    db = _session()
    school, cls, science, _sport, _t = _fixtures(db)
    _add_rule(db, school, "subject_time_window", {"subject_id": science.id, "not_after": "16:00"}, severity="blocking")
    after = _candidate(cls, science, day=models.DayOfWeek.MONDAY, start=time(16, 0), end=time(17, 0))
    violations = timetable_constraints.evaluate(db, school.id, after)
    assert violations and violations[0]["severity"] == "blocking"
    ok = _candidate(cls, science, day=models.DayOfWeek.MONDAY, start=time(14, 0), end=time(15, 0))
    assert timetable_constraints.evaluate(db, school.id, ok) == []


def test_teacher_available_days_rule():
    db = _session()
    school, cls, science, _sport, teacher = _fixtures(db)
    _add_rule(db, school, "teacher_available_days", {"teacher_id": teacher.id, "days": ["tuesday", "thursday"]})
    monday = _candidate(cls, science, day=models.DayOfWeek.MONDAY, start=time(9, 0), end=time(10, 0), teacher_id=teacher.id)
    assert timetable_constraints.evaluate(db, school.id, monday)
    tuesday = _candidate(cls, science, day=models.DayOfWeek.TUESDAY, start=time(9, 0), end=time(10, 0), teacher_id=teacher.id)
    assert timetable_constraints.evaluate(db, school.id, tuesday) == []


def test_subject_no_consecutive_days_rule():
    db = _session()
    school, cls, science, _sport, _t = _fixtures(db)
    _add_rule(db, school, "subject_no_consecutive_days", {"subject_id": science.id})
    db.add(_candidate(cls, science, day=models.DayOfWeek.MONDAY, start=time(9, 0), end=time(10, 0)))
    db.flush()
    tuesday = _candidate(cls, science, day=models.DayOfWeek.TUESDAY, start=time(9, 0), end=time(10, 0))
    assert timetable_constraints.evaluate(db, school.id, tuesday)
    thursday = _candidate(cls, science, day=models.DayOfWeek.THURSDAY, start=time(9, 0), end=time(10, 0))
    assert timetable_constraints.evaluate(db, school.id, thursday) == []


def test_subject_after_forbidden_rule():
    db = _session()
    school, cls, science, sport, _t = _fixtures(db)
    # Physics must not be placed after Sport the same day.
    _add_rule(db, school, "subject_after_forbidden", {"subject_id": science.id, "not_after_subject_id": sport.id})
    db.add(_candidate(cls, sport, day=models.DayOfWeek.MONDAY, start=time(8, 0), end=time(9, 0)))
    db.flush()
    physics_after = _candidate(cls, science, day=models.DayOfWeek.MONDAY, start=time(9, 0), end=time(10, 0))
    assert timetable_constraints.evaluate(db, school.id, physics_after)


def test_inactive_rule_is_ignored():
    db = _session()
    school, cls, science, _sport, _t = _fixtures(db)
    rule = _add_rule(db, school, "subject_time_window", {"subject_id": science.id, "not_after": "16:00"})
    rule.is_active = False
    db.flush()
    after = _candidate(cls, science, day=models.DayOfWeek.MONDAY, start=time(16, 0), end=time(17, 0))
    assert timetable_constraints.evaluate(db, school.id, after) == []
