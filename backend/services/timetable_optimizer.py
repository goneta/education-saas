"""Timetable optimiser: generate several conflict-free candidate timetables and
score them so an admin can pick the best.

In-memory and deterministic (seeded): for each seed it greedily places the
required weekly sessions on the configurable grid, enforcing hard conflicts
(class / teacher / room double-booking, teacher availability) and scoring soft
quality (fill rate, balanced heavy subjects, no same-subject back-to-back,
configured time windows). Soft penalties are driven by the database
`TimetableConstraintRule` rows, not hard-coded, so the optimiser honours each
school's configuration. The score breakdown is the seed for explainable AI
(Phase 5).
"""

from dataclasses import dataclass, field
from datetime import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from .. import models
from . import timetable_config


@dataclass
class Placement:
    class_id: int
    subject_id: int
    teacher_id: Optional[int]
    day: str
    start: time
    end: time


@dataclass
class Candidate:
    seed: int
    placements: list[Placement]
    score: float
    breakdown: dict[str, Any] = field(default_factory=dict)
    unplaced: list[dict] = field(default_factory=list)


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _rules_by_type(db: Session, school_id: int) -> dict[str, list[models.TimetableConstraintRule]]:
    grouped: dict[str, list[models.TimetableConstraintRule]] = {}
    rows = db.query(models.TimetableConstraintRule).filter(
        models.TimetableConstraintRule.school_id == school_id,
        models.TimetableConstraintRule.is_active == True,  # noqa: E712
    ).all()
    for row in rows:
        grouped.setdefault(row.rule_type, []).append(row)
    return grouped


def _teacher_allowed(rules, teacher_id, day) -> bool:
    for rule in rules.get("teacher_available_days", []):
        params = rule.parameters or {}
        if params.get("teacher_id") == teacher_id:
            allowed = {str(d).lower() for d in (params.get("days") or [])}
            if allowed and day not in allowed:
                return False
    return True


def _time_window_penalty(rules, subject_id, end: time, start: time) -> int:
    penalty = 0
    for rule in rules.get("subject_time_window", []):
        params = rule.parameters or {}
        if params.get("subject_id") != subject_id:
            continue
        not_after = params.get("not_after")
        not_before = params.get("not_before")
        if not_after and _minutes(end) > _minutes(time.fromisoformat(not_after)):
            penalty += 1
        if not_before and _minutes(start) < _minutes(time.fromisoformat(not_before)):
            penalty += 1
    return penalty


def _heavy_subject_ids(db: Session, school_id: int, min_coefficient: int) -> set[int]:
    return {
        row.id for row in db.query(models.Subject).filter(
            models.Subject.school_id == school_id,
            models.Subject.coefficient >= min_coefficient,
        ).all()
    }


def _build_candidate(db, school_id, classes, subjects, teachers, days, slots, rules, seed) -> Candidate:
    placements: list[Placement] = []
    unplaced: list[dict] = []
    # Occupancy sets keyed by (day, slot_index).
    class_busy: set[tuple] = set()
    teacher_busy: set[tuple] = set()
    # Per (class, day) subject counts for balance scoring.
    cursor = seed

    # Heavy-subject limit (first matching rule, else lenient default).
    heavy_rule = (rules.get("max_heavy_subjects_per_day") or [None])[0]
    heavy_max = int((heavy_rule.parameters or {}).get("max", 99)) if heavy_rule else 99
    heavy_min_coeff = int((heavy_rule.parameters or {}).get("min_coefficient", 3)) if heavy_rule else 3
    heavy_ids = _heavy_subject_ids(db, school_id, heavy_min_coeff) if heavy_rule else set()

    soft_penalty = 0
    required = 0
    for cls in classes:
        day_subjects: dict[str, list[int]] = {}
        day_heavy: dict[str, set] = {}
        for subject_index, subject in enumerate(subjects):
            sessions = timetable_config.weekly_sessions_for(db, school_id, subject.id, cls.id, cls.level, default=1)
            required += sessions
            for _ in range(sessions):
                placed = False
                for attempt in range(len(days) * len(slots)):
                    di = (cursor + attempt) % len(days)
                    si = ((cursor + attempt) // len(days)) % len(slots)
                    day = days[di]
                    start, end = slots[si]
                    teacher = teachers[(subject_index + attempt) % len(teachers)] if teachers else None
                    teacher_id = teacher.id if teacher else cls.main_teacher_id
                    # Hard: class/teacher not already busy this day+slot.
                    if (cls.id, day, si) in class_busy:
                        continue
                    if teacher_id and (teacher_id, day, si) in teacher_busy:
                        continue
                    if teacher_id and not _teacher_allowed(rules, teacher_id, day):
                        continue
                    placements.append(Placement(cls.id, subject.id, teacher_id, day, start, end))
                    class_busy.add((cls.id, day, si))
                    if teacher_id:
                        teacher_busy.add((teacher_id, day, si))
                    # Soft scoring.
                    soft_penalty += _time_window_penalty(rules, subject.id, end, start)
                    same = day_subjects.setdefault(day, [])
                    if subject.id in same:
                        soft_penalty += 1  # same subject repeated same day
                    same.append(subject.id)
                    if heavy_rule and subject.id in heavy_ids:
                        hs = day_heavy.setdefault(day, set())
                        hs.add(subject.id)
                        if len(hs) > heavy_max:
                            soft_penalty += 2  # too many heavy subjects that day
                    cursor += 1
                    placed = True
                    break
                if not placed:
                    unplaced.append({"class_id": cls.id, "subject_id": subject.id})

    placed_count = len(placements)
    fill_rate = (placed_count / required) if required else 1.0
    # Score in [0, 100]: fill rate dominates, soft penalties reduce it.
    score = round(max(0.0, fill_rate * 100 - soft_penalty * 2), 2)
    return Candidate(
        seed=seed,
        placements=placements,
        score=score,
        breakdown={
            "required_sessions": required,
            "placed_sessions": placed_count,
            "fill_rate": round(fill_rate, 3),
            "soft_penalty": soft_penalty,
            "unplaced": len(unplaced),
        },
        unplaced=unplaced,
    )


def generate_candidates(db: Session, school_id: int, *, candidate_count: int = 3, subject_limit: int = 12) -> list[Candidate]:
    """Return up to `candidate_count` scored candidate timetables, best first."""
    days, slots = timetable_config.effective_grid(db, school_id)
    if not days or not slots:
        return []
    classes = db.query(models.Class).filter(models.Class.school_id == school_id).order_by(models.Class.level, models.Class.name).all()
    subjects = db.query(models.Subject).filter(models.Subject.school_id == school_id).order_by(models.Subject.name).limit(subject_limit).all()
    teachers = db.query(models.User).filter(
        models.User.school_id == school_id,
        models.User.role.in_([models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR]),
    ).order_by(models.User.id).all()
    rules = _rules_by_type(db, school_id)
    candidates = [
        _build_candidate(db, school_id, classes, subjects, teachers, days, slots, rules, seed)
        for seed in range(max(1, candidate_count))
    ]
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
