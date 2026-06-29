"""Academic analytics API — automatic GPA (Slice 3, Loop 3 gap)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, security
from ..services import academics

router = APIRouter(prefix="/academics", tags=["Academic Management"])


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


@router.get("/students/{student_id}/gpa")
def student_gpa(
    student_id: int,
    term_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Automatic weighted GPA for a student (optionally a single term),
    tenant-scoped via the student's institution."""
    school_id = _school_id(current_user)
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    student_user = db.query(models.User).filter(models.User.id == student.user_id).first() if student else None
    if not student or not student_user or student_user.school_id != school_id:
        raise HTTPException(status_code=404, detail="Élève introuvable dans cet établissement")
    return academics.compute_gpa(db, student_id, term_id)
