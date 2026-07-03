"""Rentrée wizard (automation D, staff group): one flow that rolls an academic
year over.

- **Preview** (`plan_rentree`): computes, without writing anything, what the
  rollover would do — per-level promotions (using the global `SchoolLevel`
  referential's `sort_order` and the school's actual classes), leavers
  (students whose next level has no class in this school), unmapped students
  (class level absent from the referential → left untouched), and the fee
  schedules that would be cloned.
- **Run** (`run_rentree`): creates the new `AcademicYear` (making it current),
  promotes each student to a class of the next level (choosing the least-filled
  class), archives leavers (previous level/class recorded on the profile,
  class link cleared, status UNASSIGNED — accounts stay active so families keep
  portal/document access), and clones the current year's `FeeSchedule` rows to
  the new year.

Idempotence guard: the run refuses (409) when an academic year with the same
name already exists for the school, so a double-click or replayed request
cannot roll over twice.
"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import audit, models
from . import automation


def _levels_by_code(db: Session) -> dict:
    levels = db.query(models.SchoolLevel).filter(models.SchoolLevel.is_active == True).order_by(models.SchoolLevel.sort_order.asc()).all()  # noqa: E712
    return {level.code: level for level in levels}


def _next_level_code(levels_by_code: dict, code: str) -> Optional[str]:
    ordered = sorted(levels_by_code.values(), key=lambda level: (level.sort_order, level.id))
    for index, level in enumerate(ordered):
        if level.code == code:
            return ordered[index + 1].code if index + 1 < len(ordered) else None
    return None


def _school_classes_by_level(db: Session, school_id: int) -> dict:
    classes = db.query(models.Class).filter(models.Class.school_id == school_id).all()
    by_level: dict = {}
    for cls in classes:
        if cls.level:
            by_level.setdefault(cls.level, []).append(cls)
    return by_level


def _students_with_class(db: Session, school_id: int):
    return (
        db.query(models.StudentProfile, models.Class)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .join(models.Class, models.Class.id == models.StudentProfile.current_class_id)
        .filter(models.User.school_id == school_id)
        .all()
    )


def plan_rentree(db: Session, school_id: int) -> dict:
    """Dry-run: what would the rollover do? Never writes."""
    current_year = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school_id,
        models.AcademicYear.is_current == True,  # noqa: E712
    ).first()
    levels_by_code = _levels_by_code(db)
    classes_by_level = _school_classes_by_level(db, school_id)

    promotions: dict = {}
    leavers = 0
    unmapped = 0
    for profile, cls in _students_with_class(db, school_id):
        if not cls.level or cls.level not in levels_by_code:
            unmapped += 1
            continue
        next_code = _next_level_code(levels_by_code, cls.level)
        if next_code and next_code in classes_by_level:
            key = (cls.level, next_code)
            promotions[key] = promotions.get(key, 0) + 1
        else:
            leavers += 1

    fee_schedules = 0
    if current_year:
        fee_schedules = db.query(models.FeeSchedule).filter(
            models.FeeSchedule.school_id == school_id,
            models.FeeSchedule.academic_year_id == current_year.id,
        ).count()

    return {
        "current_year": current_year.name if current_year else None,
        "promotions": [
            {"level_from": level_from, "level_to": level_to, "students": count}
            for (level_from, level_to), count in sorted(promotions.items())
        ],
        "leavers": leavers,
        "unmapped": unmapped,
        "fee_schedules_to_clone": fee_schedules,
    }


def run_rentree(
    db: Session,
    school_id: int,
    current_user: models.User,
    *,
    new_year_name: str,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Execute the rollover. Refuses to run twice for the same year name."""
    existing = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school_id,
        models.AcademicYear.name == new_year_name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"L'année académique « {new_year_name} » existe déjà pour cet établissement.")
    if end_date <= start_date:
        raise HTTPException(status_code=422, detail="La date de fin doit être postérieure à la date de début.")

    previous_year = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school_id,
        models.AcademicYear.is_current == True,  # noqa: E712
    ).first()
    if previous_year:
        previous_year.is_current = False
    new_year = models.AcademicYear(name=new_year_name, start_date=start_date, end_date=end_date, is_current=True, school_id=school_id)
    db.add(new_year)
    db.flush()

    levels_by_code = _levels_by_code(db)
    classes_by_level = _school_classes_by_level(db, school_id)
    headcount = {
        cls.id: db.query(models.StudentProfile).filter(models.StudentProfile.current_class_id == cls.id).count()
        for classes in classes_by_level.values() for cls in classes
    }

    promoted, archived, unmapped = 0, 0, 0
    for profile, cls in _students_with_class(db, school_id):
        if not cls.level or cls.level not in levels_by_code:
            unmapped += 1
            continue
        profile.previous_level = cls.level
        profile.previous_class = cls.name
        next_code = _next_level_code(levels_by_code, cls.level)
        targets = classes_by_level.get(next_code) if next_code else None
        if targets:
            target = min(targets, key=lambda candidate: headcount.get(candidate.id, 0))
            profile.current_class_id = target.id
            headcount[target.id] = headcount.get(target.id, 0) + 1
            profile.status = models.StudentStatus.ASSIGNED
            promoted += 1
        else:
            profile.current_class_id = None
            profile.status = models.StudentStatus.UNASSIGNED
            archived += 1

    cloned = 0
    if previous_year:
        old_schedules = db.query(models.FeeSchedule).filter(
            models.FeeSchedule.school_id == school_id,
            models.FeeSchedule.academic_year_id == previous_year.id,
        ).all()
        for schedule in old_schedules:
            schedule.is_current = False
            db.add(models.FeeSchedule(
                name=schedule.name, amount=schedule.amount, category_order=schedule.category_order,
                is_required=schedule.is_required, is_current=True,
                academic_year_id=new_year.id, class_id=schedule.class_id, level=schedule.level,
                school_id=school_id, school_model_assignment_id=schedule.school_model_assignment_id,
            ))
            cloned += 1

    summary = {
        "new_year_id": new_year.id,
        "new_year_name": new_year_name,
        "promoted": promoted,
        "archived": archived,
        "unmapped": unmapped,
        "fee_schedules_cloned": cloned,
    }
    audit.record_audit(db, action="automation.rentree.run", current_user=current_user, entity_type="academic_year", entity_id=new_year.id, details=summary)
    automation.record_notification(
        db,
        event_type="rentree.completed",
        subject=f"Rentrée {new_year_name} exécutée",
        message=f"Rentrée {new_year_name} : {promoted} élève(s) promu(s), {archived} sortant(s) archivé(s), {unmapped} non mappé(s), {cloned} barème(s) de frais cloné(s).",
        school_id=school_id,
        recipient_user=current_user,
        source_type="automation",
        source_id=new_year.id,
        current_user=current_user,
    )
    return summary
