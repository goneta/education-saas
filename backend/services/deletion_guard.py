"""Explicit deletion policy for referenced master data (audit DATA-01).

The schema declares **no** `ON DELETE` rule while routers perform physical
deletes, so removing a referenced row could only end badly:

- on PostgreSQL a foreign-key violation surfaces as an opaque HTTP 500;
- where an ORM `cascade` happens to exist, dependent rows vanish silently —
  timetable slots, assignments, grades or fees gone with a single click, and
  almost nothing carries a `deleted_at` to recover from.

This module makes the rule explicit and uniform: **a master record that is
still referenced cannot be deleted**, and the user is told exactly what blocks
the deletion and in what quantity, in French, with a 409 (a business rule, not
a crash). Callers declare their references once; adding a new dependency is one
line in the map.
"""

from dataclasses import dataclass
from typing import Any, Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models


@dataclass(frozen=True)
class Reference:
    """One dependency: rows of `model` whose `column` points at the record."""
    model: Any
    column: str
    label: str  # user-facing, plural French label ("cours à l'emploi du temps")


def blocking_references(db: Session, references: Iterable[Reference], value: Any) -> list[tuple[str, int]]:
    """Non-empty dependencies, as (label, count) pairs."""
    blocking: list[tuple[str, int]] = []
    for reference in references:
        column = getattr(reference.model, reference.column)
        count = db.query(column).filter(column == value).count()
        if count:
            blocking.append((reference.label, count))
    return blocking


def ensure_deletable(db: Session, *, entity_label: str, references: Iterable[Reference], value: Any) -> None:
    """Raise 409 with an actionable message when the record is still referenced."""
    blocking = blocking_references(db, references, value)
    if not blocking:
        return
    details = ", ".join(f"{count} {label}" for label, count in blocking)
    raise HTTPException(
        status_code=409,
        detail=(
            f"Suppression impossible : {entity_label} est encore utilisé(e) par {details}. "
            "Supprimez ou réaffectez ces éléments d'abord."
        ),
    )


# --- Declared dependency maps -------------------------------------------------
# Deleting a class or a subject used to be guarded only against enrolled
# students (class) or not at all (subject).

CLASS_REFERENCES: tuple[Reference, ...] = (
    Reference(models.StudentProfile, "current_class_id", "élève(s) rattaché(s)"),
    Reference(models.StudentEnrollment, "class_id", "inscription(s) d'élève"),
    Reference(models.Timetable, "class_id", "cours à l'emploi du temps"),
    Reference(models.Assignment, "class_id", "devoir(s)"),
    Reference(models.Assessment, "class_id", "évaluation(s)"),
    Reference(models.ExamSession, "class_id", "session(s) d'examen"),
    Reference(models.SchoolActivity, "class_id", "activité(s)"),
    Reference(models.Fee, "class_id", "frais scolaire(s)"),
)

SUBJECT_REFERENCES: tuple[Reference, ...] = (
    Reference(models.Timetable, "subject_id", "cours à l'emploi du temps"),
    Reference(models.Assignment, "subject_id", "devoir(s)"),
    Reference(models.Assessment, "subject_id", "évaluation(s)"),
    Reference(models.ExamSession, "subject_id", "session(s) d'examen"),
)

ASSESSMENT_REFERENCES: tuple[Reference, ...] = (
    Reference(models.Grade, "assessment_id", "note(s) saisie(s)"),
)
