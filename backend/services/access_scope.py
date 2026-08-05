"""Intra-tenant authorization — WHICH students a user may see inside their school.

Audit PRIV-01 / PRIV-02: isolation *between* schools was solid and tested, but
inside a school many endpoints only checked "same school". A logged-in student
could therefore read another student's discipline record, boarding assignment or
GPA by walking identifiers.

This module is the single source of truth for the row-level rule:

- **staff** (administration, direction, teachers, life-of-school roles) see every
  student of their school — the existing school scoping still applies;
- **students / pupils** see only themselves;
- **parents** see only their linked children (`ParentStudentLink`);
- anyone else sees nothing.

`visible_student_ids` returns ``None`` for "no row-level restriction" so callers
can skip the extra filter entirely for staff.
"""

from typing import Optional

from sqlalchemy.orm import Session

from .. import models

# Roles that legitimately work on the whole student body of their school.
STAFF_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.DIRECTOR,
    models.UserRole.PRINCIPAL,
    models.UserRole.DEPARTMENT_HEAD,
    models.UserRole.PEDAGOGY_COORDINATOR,
    models.UserRole.EDUCATOR,
    models.UserRole.REGISTRAR,
    models.UserRole.SECRETARY,
    models.UserRole.RECEPTIONIST,
    models.UserRole.ACCOUNTANT,
    models.UserRole.CASHIER,
    models.UserRole.TEACHER,
    models.UserRole.TRAINER,
    models.UserRole.INSTRUCTOR,
    models.UserRole.STAFF,
}

LEARNER_ROLES = {models.UserRole.STUDENT, models.UserRole.PUPIL}


def is_staff(user: models.User) -> bool:
    return user.role in STAFF_ROLES


def own_student_id(db: Session, user: models.User) -> Optional[int]:
    """The student profile id of a learner account (None for other roles)."""
    if user.role not in LEARNER_ROLES:
        return None
    profile = (
        db.query(models.StudentProfile.id)
        .filter(models.StudentProfile.user_id == user.id)
        .first()
    )
    return profile[0] if profile else None


def linked_child_ids(db: Session, user: models.User) -> list[int]:
    """Student profile ids a parent account is linked to."""
    if user.role != models.UserRole.PARENT:
        return []
    rows = (
        db.query(models.ParentStudentLink.student_id)
        .filter(models.ParentStudentLink.parent_user_id == user.id)
        .all()
    )
    return [row[0] for row in rows if row[0] is not None]


def visible_student_ids(db: Session, user: models.User) -> Optional[set[int]]:
    """Student profile ids the user may see.

    ``None`` means "no row-level restriction" (staff). An empty set means the
    user may see nothing — callers must return an empty result, never all rows.
    """
    if is_staff(user):
        return None
    if user.role in LEARNER_ROLES:
        own = own_student_id(db, user)
        return {own} if own else set()
    if user.role == models.UserRole.PARENT:
        return set(linked_child_ids(db, user))
    return set()


def can_view_student(db: Session, user: models.User, student_id: int) -> bool:
    """May this user see data about that specific student?

    School scoping remains the caller's responsibility — this answers the
    row-level question only.
    """
    allowed = visible_student_ids(db, user)
    return allowed is None or student_id in allowed
