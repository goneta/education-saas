from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from .. import models


@dataclass(frozen=True)
class ActiveSchoolContext:
    organization_id: int
    school_id: int
    school_model_assignment_id: int
    academic_year_id: Optional[int]


def user_can_access_school(db: Session, user: models.User, school: models.School) -> bool:
    if user.role == models.UserRole.SUPER_ADMIN:
        return True
    if user.school_id == school.id:
        return True
    if school.organization_id and db.query(models.Organization.id).filter(
        models.Organization.id == school.organization_id,
        models.Organization.owner_user_id == user.id,
        models.Organization.is_active == True,  # noqa: E712
    ).first():
        return True
    return db.query(models.SchoolMembership.id).filter(
        models.SchoolMembership.user_id == user.id,
        models.SchoolMembership.school_id == school.id,
        models.SchoolMembership.is_active == True,  # noqa: E712
    ).first() is not None


def accessible_schools_query(db: Session, user: models.User):
    query = db.query(models.School).filter(models.School.is_active == True)  # noqa: E712
    if user.role == models.UserRole.SUPER_ADMIN:
        return query
    owned_organization_ids = db.query(models.Organization.id).filter(
        models.Organization.owner_user_id == user.id,
        models.Organization.is_active == True,  # noqa: E712
    )
    membership_school_ids = db.query(models.SchoolMembership.school_id).filter(
        models.SchoolMembership.user_id == user.id,
        models.SchoolMembership.is_active == True,  # noqa: E712
    )
    allowed = [row[0] for row in membership_school_ids.all()]
    if user.school_id:
        allowed.append(user.school_id)
    return query.filter(
        (models.School.organization_id.in_(owned_organization_ids))
        | (models.School.id.in_(set(allowed) or {-1}))
    )


def resolve_context(
    db: Session,
    user: models.User,
    *,
    school_model_assignment_id: Optional[int] = None,
    academic_year_id: Optional[int] = None,
) -> ActiveSchoolContext:
    preference = db.query(models.UserPreference).filter(models.UserPreference.user_id == user.id).first()
    assignment_id = school_model_assignment_id or (
        preference.active_school_model_assignment_id if preference else None
    )
    if not assignment_id and user.school_id:
        assignment_id = db.query(models.SchoolModelAssignment.id).filter(
            models.SchoolModelAssignment.school_id == user.school_id,
            models.SchoolModelAssignment.is_active == True,  # noqa: E712
        ).order_by(models.SchoolModelAssignment.id).scalar()
    if not assignment_id:
        raise HTTPException(status_code=400, detail="Selectionnez un modele d'etablissement actif.")

    assignment = db.query(models.SchoolModelAssignment).filter(
        models.SchoolModelAssignment.id == assignment_id,
        models.SchoolModelAssignment.is_active == True,  # noqa: E712
    ).first()
    if not assignment or not user_can_access_school(db, user, assignment.school):
        raise HTTPException(status_code=403, detail="Contexte scolaire non autorise.")
    if not assignment.school.organization_id:
        raise HTTPException(status_code=409, detail="L'etablissement n'est rattache a aucune organisation.")

    year_id = academic_year_id or (preference.active_academic_year_id if preference else None)
    if year_id:
        year = db.query(models.AcademicYear).filter(
            models.AcademicYear.id == year_id,
            models.AcademicYear.school_id == assignment.school_id,
        ).first()
        if not year:
            raise HTTPException(status_code=403, detail="Annee academique hors du contexte actif.")
    else:
        year_id = db.query(models.AcademicYear.id).filter(
            models.AcademicYear.school_id == assignment.school_id,
            models.AcademicYear.school_model_assignment_id == assignment.id,
            models.AcademicYear.is_current == True,  # noqa: E712
        ).order_by(models.AcademicYear.id.desc()).scalar()

    return ActiveSchoolContext(
        organization_id=assignment.school.organization_id,
        school_id=assignment.school_id,
        school_model_assignment_id=assignment.id,
        academic_year_id=year_id,
    )


def context_from_headers(
    db: Session,
    user: models.User,
    x_school_model_assignment_id: Optional[int] = Header(default=None, alias="X-School-Model-Assignment-ID"),
    x_academic_year_id: Optional[int] = Header(default=None, alias="X-Academic-Year-ID"),
) -> ActiveSchoolContext:
    return resolve_context(
        db,
        user,
        school_model_assignment_id=x_school_model_assignment_id,
        academic_year_id=x_academic_year_id,
    )
