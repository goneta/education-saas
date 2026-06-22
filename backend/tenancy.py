from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from . import models


SCHOOL_REQUIRED_MESSAGE = "Vous devez d'abord créer ou être associé à un établissement scolaire avant de pouvoir ajouter des éléments."
SUPER_ADMIN_SELECT_SCHOOL_MESSAGE = "Veuillez sélectionner une école avant de créer cet élément."


def is_super_admin(user: models.User) -> bool:
    return user.role == models.UserRole.SUPER_ADMIN


def require_school_scope(current_user: models.User) -> int:
    if is_super_admin(current_user):
        raise HTTPException(status_code=400, detail=SUPER_ADMIN_SELECT_SCHOOL_MESSAGE)
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail=SCHOOL_REQUIRED_MESSAGE)
    return current_user.school_id


def resolve_school_id_for_create(current_user: models.User, payload_school_id: Optional[int], db: Optional[Session] = None) -> int:
    if is_super_admin(current_user):
        if not payload_school_id:
            raise HTTPException(status_code=400, detail=SUPER_ADMIN_SELECT_SCHOOL_MESSAGE)
        _assert_school_exists(db, payload_school_id)
        return payload_school_id
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail=SCHOOL_REQUIRED_MESSAGE)
    if payload_school_id and payload_school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez pas créer ou modifier des données pour une autre école.")
    _assert_school_exists(db, current_user.school_id)
    return current_user.school_id


def apply_school_filter(query: Any, model: Any, current_user: models.User, school_id: Optional[int] = None):
    if is_super_admin(current_user):
        return query.filter(model.school_id == school_id) if school_id else query
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail=SCHOOL_REQUIRED_MESSAGE)
    return query.filter(model.school_id == current_user.school_id)


def apply_user_school_filter(query: Any, current_user: models.User, school_id: Optional[int] = None):
    if is_super_admin(current_user):
        return query.filter(models.User.school_id == school_id) if school_id else query
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail=SCHOOL_REQUIRED_MESSAGE)
    return query.filter(models.User.school_id == current_user.school_id)


def find_existing_person(
    db: Session,
    *,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    numref: Optional[str] = None,
    registration_number: Optional[str] = None,
    full_name: Optional[str] = None,
    date_of_birth: Optional[datetime] = None,
) -> Optional[models.User]:
    strong_predicates = []
    if email:
        strong_predicates.append(models.User.email == email)
    if phone:
        strong_predicates.append(or_(models.User.phone_number == phone, models.User.phone_e164 == phone))
    if numref:
        strong_predicates.append(models.User.numref == numref)
    if registration_number:
        strong_predicates.append(models.StudentProfile.registration_number == registration_number)
    if strong_predicates:
        return db.query(models.User).outerjoin(models.StudentProfile).filter(or_(*strong_predicates)).first()
    if not (full_name and date_of_birth):
        return None
    return db.query(models.User).outerjoin(models.StudentProfile).filter(
        and_(models.User.full_name == full_name, models.StudentProfile.date_of_birth == date_of_birth)
    ).first()


def create_or_transfer_school_membership(
    db: Session,
    *,
    user: models.User,
    school_id: int,
    role: str,
    transfer_reason: Optional[str] = None,
    start_date: Optional[datetime] = None,
) -> models.SchoolMembership:
    start_date = start_date or datetime.utcnow()
    active_rows = db.query(models.SchoolMembership).filter(
        models.SchoolMembership.user_id == user.id,
        models.SchoolMembership.is_active == True,  # noqa: E712
    ).all()
    existing_target = None
    for row in active_rows:
        if row.school_id == school_id and row.role == role:
            existing_target = row
        else:
            row.end_date = start_date
            row.is_active = False
            row.membership_status = "transferred"
            if transfer_reason:
                row.transfer_reason = transfer_reason
    if existing_target:
        return existing_target
    membership = models.SchoolMembership(
        user_id=user.id,
        school_id=school_id,
        role=role,
        start_date=start_date,
        is_active=True,
        membership_status="active",
        transfer_reason=transfer_reason,
    )
    db.add(membership)
    db.flush()
    return membership


def _assert_school_exists(db: Optional[Session], school_id: Optional[int]) -> None:
    if not db or not school_id:
        return
    if not db.query(models.School.id).filter(models.School.id == school_id).first():
        raise HTTPException(status_code=404, detail="École introuvable")
