from datetime import datetime, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import timetable_config


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    school = models.School(name="Grid", domain_prefix="grid", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    return school


def test_effective_grid_defaults_when_no_config():
    db = _session()
    school = _school(db)
    days, slots = timetable_config.effective_grid(db, school.id)
    assert days == timetable_config.DEFAULT_WORKING_DAYS
    # Only course slots are schedulable (break/lunch excluded).
    assert all(isinstance(s[0], time) for s in slots)
    assert len(slots) == sum(1 for s in timetable_config.DEFAULT_SLOTS if s["kind"] == "course")


def test_effective_grid_uses_config_and_excludes_breaks():
    db = _session()
    school = _school(db)
    db.add(models.TimetableConfig(
        school_id=school.id, is_active=True,
        working_days=["monday", "saturday"],
        slots=[
            {"start": "07:00", "end": "08:00", "kind": "course"},
            {"start": "08:00", "end": "08:15", "kind": "break"},
            {"start": "08:15", "end": "09:15", "kind": "course"},
        ],
    ))
    db.commit()
    days, slots = timetable_config.effective_grid(db, school.id)
    assert days == ["monday", "saturday"]
    assert len(slots) == 2  # break excluded
    assert slots[0] == (time(7, 0), time(8, 0))


def test_weekly_sessions_prefers_class_then_level_then_default():
    db = _session()
    school = _school(db)
    cls = models.Class(name="6A", level="6", school_id=school.id)
    subject = models.Subject(name="Maths", code="M", school_id=school.id)
    db.add_all([cls, subject])
    db.flush()
    # Default when nothing configured.
    assert timetable_config.weekly_sessions_for(db, school.id, subject.id, cls.id, cls.level) == 1
    db.add(models.SubjectRequirement(school_id=school.id, subject_id=subject.id, level="6", weekly_sessions=3))
    db.add(models.SubjectRequirement(school_id=school.id, subject_id=subject.id, class_id=cls.id, weekly_sessions=5))
    db.commit()
    # Class-specific wins over level.
    assert timetable_config.weekly_sessions_for(db, school.id, subject.id, cls.id, cls.level) == 5
    # Another class at the same level falls back to the level rule.
    assert timetable_config.weekly_sessions_for(db, school.id, subject.id, 999, "6") == 3


def test_holiday_lookup():
    db = _session()
    school = _school(db)
    db.add(models.SchoolHoliday(school_id=school.id, date=datetime(2026, 5, 1), name="Fete du travail"))
    db.commit()
    assert timetable_config.is_holiday(db, school.id, datetime(2026, 5, 1).date())
    assert not timetable_config.is_holiday(db, school.id, datetime(2026, 5, 2).date())
