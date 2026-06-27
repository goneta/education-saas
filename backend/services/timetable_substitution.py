"""Automatic substitute proposals for an absent teacher.

For each course the absent teacher gives on a weekday, propose substitute
teachers who are free at that slot and allowed to teach that day (honouring the
`teacher_available_days` constraint rule). Read-only: proposals are returned for
an admin to apply; nothing is mutated here.
"""

from typing import Optional

from sqlalchemy.orm import Session

from .. import models

TEACHING_ROLES = [models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR]


def _day_value(value) -> str:
    return str(getattr(value, "value", value)).lower()


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def _teacher_available(rules, teacher_id, day) -> bool:
    for rule in rules:
        params = rule.parameters or {}
        if params.get("teacher_id") == teacher_id:
            allowed = {str(d).lower() for d in (params.get("days") or [])}
            if allowed and day not in allowed:
                return False
    return True


def propose_substitutions(db: Session, school_id: int, teacher_id: int, weekday: str) -> list[dict]:
    """Return, per affected course on `weekday`, the available substitute teachers."""
    weekday = weekday.lower()
    affected = [
        row for row in db.query(models.Timetable).join(models.Class).filter(
            models.Class.school_id == school_id,
            models.Timetable.teacher_id == teacher_id,
        ).all()
        if _day_value(row.day_of_week) == weekday
    ]
    if not affected:
        return []

    teachers = db.query(models.User).filter(
        models.User.school_id == school_id,
        models.User.role.in_(TEACHING_ROLES),
        models.User.id != teacher_id,
        models.User.is_active == True,  # noqa: E712
    ).all()
    availability_rules = db.query(models.TimetableConstraintRule).filter(
        models.TimetableConstraintRule.school_id == school_id,
        models.TimetableConstraintRule.rule_type == "teacher_available_days",
        models.TimetableConstraintRule.is_active == True,  # noqa: E712
    ).all()
    # Preload each teacher's busy intervals on the weekday.
    busy: dict[int, list] = {}
    for row in db.query(models.Timetable).join(models.Class).filter(models.Class.school_id == school_id).all():
        if _day_value(row.day_of_week) == weekday and row.teacher_id:
            busy.setdefault(row.teacher_id, []).append((row.start_time, row.end_time))

    proposals = []
    for entry in affected:
        candidates = []
        for teacher in teachers:
            if not _teacher_available(availability_rules, teacher.id, weekday):
                continue
            conflict = any(_overlaps(entry.start_time, entry.end_time, bs, be) for bs, be in busy.get(teacher.id, []))
            if conflict:
                continue
            candidates.append({"teacher_id": teacher.id, "full_name": teacher.full_name})
        proposals.append({
            "timetable_id": entry.id,
            "class_id": entry.class_id,
            "subject_id": entry.subject_id,
            "start_time": entry.start_time.isoformat(),
            "end_time": entry.end_time.isoformat(),
            "substitutes": candidates,
        })
    return proposals
