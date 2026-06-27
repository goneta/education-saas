"""Helpers for multi-school teaching assignments.

A teacher (one `TeacherProfile`, unique per user) can hold several active
`TeacherAssignment` rows, one per school/model they teach at. A teacher is
"in" a school when they have an active assignment there, regardless of their
primary `User.school_id`.
"""

from typing import Optional

from sqlalchemy.orm import Session

from .. import models


def active_assignment_in_school(db: Session, user_id: int, school_id: int) -> Optional[models.TeacherAssignment]:
    return db.query(models.TeacherAssignment).filter(
        models.TeacherAssignment.user_id == user_id,
        models.TeacherAssignment.school_id == school_id,
        models.TeacherAssignment.is_active == True,  # noqa: E712
    ).first()


def teacher_accessible(db: Session, teacher_user_id: int, current_user: models.User) -> bool:
    """A super admin can reach any teacher; a school user only a teacher who
    holds an active assignment in their school."""
    if current_user.role == models.UserRole.SUPER_ADMIN:
        return True
    if not current_user.school_id:
        return False
    return active_assignment_in_school(db, teacher_user_id, current_user.school_id) is not None


def ensure_assignment(
    db: Session,
    *,
    user_id: int,
    school_id: int,
    school_model_assignment_id: Optional[int],
    specialization: Optional[str] = None,
    employment_type: str = "full_time",
    created_by_user_id: Optional[int] = None,
) -> models.TeacherAssignment:
    """Idempotently attach a teacher to a school/model. Reactivates a prior
    (possibly ended) assignment instead of creating a duplicate. The teacher's
    first assignment is flagged primary."""
    existing = db.query(models.TeacherAssignment).filter(
        models.TeacherAssignment.user_id == user_id,
        models.TeacherAssignment.school_model_assignment_id == school_model_assignment_id,
    ).first()
    if existing:
        existing.is_active = True
        existing.end_date = None
        if specialization:
            existing.specialization = specialization
        existing.employment_type = employment_type
        return existing
    has_any = db.query(models.TeacherAssignment.id).filter(
        models.TeacherAssignment.user_id == user_id
    ).first() is not None
    assignment = models.TeacherAssignment(
        user_id=user_id,
        school_id=school_id,
        school_model_assignment_id=school_model_assignment_id,
        employment_type=employment_type,
        specialization=specialization,
        is_primary=not has_any,
        is_active=True,
        created_by_user_id=created_by_user_id,
    )
    db.add(assignment)
    db.flush()
    return assignment
