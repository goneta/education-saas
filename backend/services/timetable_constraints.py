"""Configurable timetable constraint engine.

No pedagogical rule is hard-coded here: the rules live in
`TimetableConstraintRule` rows and are interpreted by the handlers below by
`rule_type`. Each handler receives the candidate placement, the rule parameters,
and helpers to inspect the rest of the class's day/week, and returns zero or more
violations. Every violation carries a human-readable `message` (the explainable
reason) plus the originating `rule_id` and `severity`.

Built-in hard conflicts (class/teacher/room double-booking, time window) stay in
the router; this engine adds the admin-configurable pedagogical/human rules.
"""

from datetime import time
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from .. import models

DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _day_value(value: Any) -> str:
    return str(getattr(value, "value", value)).lower()


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _parse_time(value: Optional[str]) -> Optional[time]:
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        return None


def active_rules(db: Session, school_id: int) -> list[models.TimetableConstraintRule]:
    return db.query(models.TimetableConstraintRule).filter(
        models.TimetableConstraintRule.is_active == True,  # noqa: E712
        models.TimetableConstraintRule.school_id == school_id,
    ).all()


def _class_day_entries(db: Session, school_id: int, class_id: int, day: str, exclude_id: Optional[int]):
    rows = db.query(models.Timetable).filter(
        models.Timetable.class_id == class_id,
    ).all()
    result = []
    for row in rows:
        if exclude_id and row.id == exclude_id:
            continue
        if _day_value(row.day_of_week) == day:
            result.append(row)
    return result


def _class_week_days_for_subject(db: Session, class_id: int, subject_id: int, exclude_id: Optional[int]) -> set[str]:
    rows = db.query(models.Timetable).filter(
        models.Timetable.class_id == class_id,
        models.Timetable.subject_id == subject_id,
    ).all()
    return {_day_value(row.day_of_week) for row in rows if not (exclude_id and row.id == exclude_id)}


# --- rule handlers -----------------------------------------------------------

def _subject_time_window(db, school_id, candidate, rule, exclude_id):
    params = rule.parameters or {}
    if candidate.subject_id != params.get("subject_id"):
        return []
    violations = []
    not_after = _parse_time(params.get("not_after"))
    not_before = _parse_time(params.get("not_before"))
    if not_after and _minutes(candidate.end_time) > _minutes(not_after):
        violations.append(f"Cette matière ne doit pas être programmée après {params['not_after']}.")
    if not_before and _minutes(candidate.start_time) < _minutes(not_before):
        violations.append(f"Cette matière ne doit pas être programmée avant {params['not_before']}.")
    return violations


def _subject_no_consecutive_days(db, school_id, candidate, rule, exclude_id):
    params = rule.parameters or {}
    if candidate.subject_id != params.get("subject_id"):
        return []
    day = _day_value(candidate.day_of_week)
    if day not in DAY_ORDER:
        return []
    idx = DAY_ORDER.index(day)
    neighbours = {DAY_ORDER[i] for i in (idx - 1, idx + 1) if 0 <= i < len(DAY_ORDER)}
    used = _class_week_days_for_subject(db, candidate.class_id, candidate.subject_id, exclude_id)
    if used & neighbours:
        return ["Cette matière ne doit pas être enseignée deux jours consécutifs."]
    return []


def _subject_after_forbidden(db, school_id, candidate, rule, exclude_id):
    params = rule.parameters or {}
    if candidate.subject_id != params.get("subject_id"):
        return []
    forbidden_before = params.get("not_after_subject_id")
    if not forbidden_before:
        return []
    day = _day_value(candidate.day_of_week)
    for other in _class_day_entries(db, school_id, candidate.class_id, day, exclude_id):
        if other.subject_id == forbidden_before and _minutes(other.end_time) <= _minutes(candidate.start_time):
            return ["Cette matière ne doit pas être placée après la matière indiquée le même jour."]
    return []


def _teacher_available_days(db, school_id, candidate, rule, exclude_id):
    params = rule.parameters or {}
    if not candidate.teacher_id or candidate.teacher_id != params.get("teacher_id"):
        return []
    allowed = {str(d).lower() for d in (params.get("days") or [])}
    if allowed and _day_value(candidate.day_of_week) not in allowed:
        return [f"Cet enseignant n'est disponible que les: {', '.join(sorted(allowed))}."]
    return []


def _subject_max_per_day(db, school_id, candidate, rule, exclude_id):
    params = rule.parameters or {}
    if candidate.subject_id != params.get("subject_id"):
        return []
    max_count = int(params.get("max", 1))
    day = _day_value(candidate.day_of_week)
    same = [e for e in _class_day_entries(db, school_id, candidate.class_id, day, exclude_id) if e.subject_id == candidate.subject_id]
    if len(same) + 1 > max_count:
        return [f"Cette matière ne peut pas dépasser {max_count} séance(s) par jour pour cette classe."]
    return []


def _max_heavy_subjects_per_day(db, school_id, candidate, rule, exclude_id):
    params = rule.parameters or {}
    max_count = int(params.get("max", 2))
    min_coefficient = int(params.get("min_coefficient", 3))
    heavy_ids = {
        row.id for row in db.query(models.Subject).filter(
            models.Subject.school_id == school_id,
            models.Subject.coefficient >= min_coefficient,
        ).all()
    }
    if candidate.subject_id not in heavy_ids:
        return []
    day = _day_value(candidate.day_of_week)
    heavy_subjects = {candidate.subject_id}
    for entry in _class_day_entries(db, school_id, candidate.class_id, day, exclude_id):
        if entry.subject_id in heavy_ids:
            heavy_subjects.add(entry.subject_id)
    if len(heavy_subjects) > max_count:
        return [f"Pas plus de {max_count} matière(s) lourde(s) par jour pour cette classe."]
    return []


def _room_subject_restriction(db, school_id, candidate, rule, exclude_id):
    params = rule.parameters or {}
    room = (params.get("room") or "").strip().lower()
    candidate_room = (getattr(candidate, "room", "") or "").strip().lower()
    if not room or candidate_room != room:
        return []
    allowed = set(params.get("subject_ids") or [])
    if allowed and candidate.subject_id not in allowed:
        return [f"La salle « {params.get('room')} » est réservée à certaines matières."]
    return []


HANDLERS: dict[str, Callable] = {
    "subject_time_window": _subject_time_window,
    "subject_no_consecutive_days": _subject_no_consecutive_days,
    "subject_after_forbidden": _subject_after_forbidden,
    "teacher_available_days": _teacher_available_days,
    "subject_max_per_day": _subject_max_per_day,
    "max_heavy_subjects_per_day": _max_heavy_subjects_per_day,
    "room_subject_restriction": _room_subject_restriction,
}

SUPPORTED_RULE_TYPES = sorted(HANDLERS.keys())


def evaluate(db: Session, school_id: int, candidate, exclude_id: Optional[int] = None) -> list[dict]:
    """Evaluate the candidate placement against the school's active configurable
    rules. Returns a list of violations with explanations."""
    violations: list[dict] = []
    for rule in active_rules(db, school_id):
        handler = HANDLERS.get(rule.rule_type)
        if not handler:
            continue
        for message in handler(db, school_id, candidate, rule, exclude_id):
            violations.append({
                "type": rule.rule_type,
                "severity": rule.severity if rule.severity in {"blocking", "warning"} else "warning",
                "message": message,
                "rule_id": rule.id,
                "rule_name": rule.name,
            })
    return violations
