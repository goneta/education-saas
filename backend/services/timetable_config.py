"""Configurable scheduling grid: working days, time slots (course/break/lunch),
weekly subject volume and holidays. Generation reads these instead of hard-coded
days/slots, with sensible defaults when a school has not configured anything yet.
"""

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy.orm import Session

from .. import models

DEFAULT_WORKING_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
DEFAULT_SLOTS = [
    {"start": "08:00", "end": "10:00", "kind": "course"},
    {"start": "10:00", "end": "10:15", "kind": "break"},
    {"start": "10:15", "end": "12:15", "kind": "course"},
    {"start": "12:15", "end": "14:00", "kind": "lunch"},
    {"start": "14:00", "end": "16:00", "kind": "course"},
]


def _parse(value: str) -> time:
    return time.fromisoformat(value)


def active_config(db: Session, school_id: int, school_model_assignment_id: Optional[int] = None) -> Optional[models.TimetableConfig]:
    query = db.query(models.TimetableConfig).filter(
        models.TimetableConfig.school_id == school_id,
        models.TimetableConfig.is_active == True,  # noqa: E712
    )
    if school_model_assignment_id is not None:
        scoped = query.filter(models.TimetableConfig.school_model_assignment_id == school_model_assignment_id).first()
        if scoped:
            return scoped
    return query.order_by(models.TimetableConfig.id.desc()).first()


def effective_grid(db: Session, school_id: int, school_model_assignment_id: Optional[int] = None):
    """Return (working_days: list[str], course_slots: list[(time, time)]).

    Only `course` slots are schedulable; break/lunch slots are excluded.
    Falls back to sensible defaults when no config exists.
    """
    config = active_config(db, school_id, school_model_assignment_id)
    raw_days = (config.working_days if config and config.working_days else DEFAULT_WORKING_DAYS)
    raw_slots = (config.slots if config and config.slots else DEFAULT_SLOTS)
    working_days = [str(day).lower() for day in raw_days]
    course_slots = [
        (_parse(slot["start"]), _parse(slot["end"]))
        for slot in raw_slots
        if (slot.get("kind") or "course") == "course" and slot.get("start") and slot.get("end")
    ]
    return working_days, course_slots


def weekly_sessions_for(db: Session, school_id: int, subject_id: int, class_id: Optional[int], level: Optional[str], default: int = 1) -> int:
    """Configured weekly sessions for a subject, preferring a class-specific rule,
    then a level rule, then the default."""
    rows = db.query(models.SubjectRequirement).filter(
        models.SubjectRequirement.school_id == school_id,
        models.SubjectRequirement.subject_id == subject_id,
    ).all()
    for row in rows:
        if class_id is not None and row.class_id == class_id:
            return max(0, row.weekly_sessions)
    for row in rows:
        if row.class_id is None and level is not None and (row.level or "").lower() == level.lower():
            return max(0, row.weekly_sessions)
    return default


def holiday_dates(db: Session, school_id: int) -> set[date]:
    return {
        (row.date.date() if isinstance(row.date, datetime) else row.date)
        for row in db.query(models.SchoolHoliday).filter(models.SchoolHoliday.school_id == school_id).all()
    }


def is_holiday(db: Session, school_id: int, day: date) -> bool:
    return day in holiday_dates(db, school_id)
