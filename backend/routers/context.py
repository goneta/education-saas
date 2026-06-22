from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import audit, database, localization, models, rbac, schemas, security
from ..services import school_context, school_model_templates


router = APIRouter(prefix="/context", tags=["Multi-school context"])


def _preference(db: Session, user: models.User) -> models.UserPreference:
    row = db.query(models.UserPreference).filter(models.UserPreference.user_id == user.id).first()
    if not row:
        row = models.UserPreference(user_id=user.id)
        db.add(row)
        db.flush()
    return row


def _assignment_payload(assignment: models.SchoolModelAssignment) -> dict:
    return {
        "id": assignment.id,
        "school_id": assignment.school_id,
        "school_name": assignment.school.name,
        "organization_id": assignment.school.organization_id,
        "organization_name": assignment.school.organization.name if assignment.school.organization else None,
        "school_model_id": assignment.school_model_id,
        "model_code": assignment.school_model.code,
        "model_name": assignment.school_model.name,
        "display_name": assignment.display_name or assignment.school_model.name,
        "is_active": assignment.is_active,
        "ai_enabled": assignment.ai_enabled,
        "monthly_ai_credit_limit": assignment.monthly_ai_credit_limit,
    }


@router.post("/organizations")
def create_organization(
    payload: schemas.OrganizationCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Administrateur uniquement.")
    row = models.Organization(
        **payload.model_dump(),
        owner_user_id=current_user.id,
        is_active=True,
    )
    db.add(row)
    db.flush()
    audit.record_audit(
        db,
        action="organization.created",
        current_user=current_user,
        entity_type="organization",
        entity_id=row.id,
        details={"name": row.name},
    )
    db.commit()
    return {"id": row.id, "name": row.name, "is_active": row.is_active}


@router.post("/schools")
def create_organization_school(
    payload: schemas.OrganizationSchoolCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    organization = db.query(models.Organization).filter(
        models.Organization.id == payload.organization_id,
        models.Organization.is_active == True,  # noqa: E712
    ).first()
    if not organization or (
        current_user.role != models.UserRole.SUPER_ADMIN
        and organization.owner_user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Organisation non autorisee.")
    if db.query(models.School.id).filter(models.School.domain_prefix == payload.school.domain_prefix).first():
        raise HTTPException(status_code=409, detail="Ce code d'etablissement est deja utilise.")
    country_profile = localization.country_profile(payload.school.country_code)
    school = models.School(
        organization_id=organization.id,
        name=payload.school.name,
        domain_prefix=payload.school.domain_prefix,
        school_type=payload.school.school_type,
        address=payload.school.address,
        phone=payload.school.phone,
        email=payload.school.email,
        website=payload.school.website,
        logo_url=payload.school.logo_url,
        registration_number=payload.school.registration_number,
        country_code=country_profile["country_code"],
        default_currency=payload.school.default_currency or country_profile["currency"],
        currency_code=payload.school.currency_code or country_profile["currency_code"],
        primary_language=payload.school.primary_language or country_profile["locale"],
        timezone=payload.school.timezone or country_profile["timezone"],
        date_format=payload.school.date_format or country_profile["date_format"],
        time_format=payload.school.time_format or country_profile["time_format"],
        formatted_address=payload.school.address,
        is_active=True,
    )
    db.add(school)
    db.flush()
    _organization, assignments, seeded = school_model_templates.ensure_school_foundation(
        db,
        school,
        owner_user_id=organization.owner_user_id,
        model_codes=payload.model_codes,
        seed_defaults=payload.seed_defaults,
    )
    audit.record_audit(
        db,
        action="organization.school_created",
        current_user=current_user,
        entity_type="school",
        entity_id=school.id,
        details={"organization_id": organization.id, "model_codes": payload.model_codes, "seeded": seeded},
    )
    db.commit()
    return {
        "id": school.id,
        "organization_id": organization.id,
        "name": school.name,
        "assignments": [_assignment_payload(row) for row in assignments],
        "seeded": seeded,
    }


@router.get("/catalog")
def model_catalog(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    return [
        {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "description": row.description,
            "is_system_template": row.is_system_template,
            "is_active": row.is_active,
        }
        for row in db.query(models.SchoolModel).filter(
            models.SchoolModel.is_active == True,  # noqa: E712
        ).order_by(models.SchoolModel.id).all()
    ]


@router.get("/options")
def context_options(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    schools = school_context.accessible_schools_query(db, current_user).options(
        joinedload(models.School.organization),
        joinedload(models.School.model_assignments).joinedload(models.SchoolModelAssignment.school_model),
    ).order_by(models.School.name).all()
    school_ids = [school.id for school in schools]
    years = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id.in_(school_ids or [-1])
    ).order_by(models.AcademicYear.start_date.desc()).all()
    return {
        "organizations": [
            {
                "id": school.organization.id,
                "name": school.organization.name,
                "is_owner": current_user.role == models.UserRole.SUPER_ADMIN or school.organization.owner_user_id == current_user.id,
            }
            for school in schools
            if school.organization
        ],
        "schools": [
            {
                "id": school.id,
                "organization_id": school.organization_id,
                "name": school.name,
                "code": school.domain_prefix,
            }
            for school in schools
        ],
        "assignments": [
            _assignment_payload(assignment)
            for school in schools
            for assignment in school.model_assignments
            if assignment.is_active and assignment.school_model.is_active
        ],
        "academic_years": [
            {
                "id": year.id,
                "school_id": year.school_id,
                "school_model_assignment_id": year.school_model_assignment_id,
                "name": year.name,
                "is_current": year.is_current,
            }
            for year in years
        ],
    }


@router.get("/active")
def active_context(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    context = school_context.resolve_context(db, current_user)
    assignment = db.query(models.SchoolModelAssignment).options(
        joinedload(models.SchoolModelAssignment.school).joinedload(models.School.organization),
        joinedload(models.SchoolModelAssignment.school_model),
    ).filter(models.SchoolModelAssignment.id == context.school_model_assignment_id).first()
    payload = _assignment_payload(assignment)
    payload["academic_year_id"] = context.academic_year_id
    if context.academic_year_id:
        year = db.query(models.AcademicYear).filter(models.AcademicYear.id == context.academic_year_id).first()
        payload["academic_year_name"] = year.name if year else None
    return payload


@router.put("/active")
def update_active_context(
    payload: schemas.SchoolContextUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    context = school_context.resolve_context(
        db,
        current_user,
        school_model_assignment_id=payload.school_model_assignment_id,
        academic_year_id=payload.academic_year_id,
    )
    preference = _preference(db, current_user)
    old = {
        "organization_id": preference.active_organization_id,
        "school_id": preference.active_school_id,
        "school_model_assignment_id": preference.active_school_model_assignment_id,
        "academic_year_id": preference.active_academic_year_id,
    }
    preference.active_organization_id = context.organization_id
    preference.active_school_id = context.school_id
    preference.active_school_model_assignment_id = context.school_model_assignment_id
    preference.active_academic_year_id = context.academic_year_id
    audit.record_audit(
        db,
        action="context.changed",
        current_user=current_user,
        entity_type="school_model_assignment",
        entity_id=context.school_model_assignment_id,
        details={"old": old, "new": context.__dict__},
    )
    db.commit()
    return active_context(current_user=current_user, db=db)


@router.post("/assignments")
def create_assignments(
    payload: schemas.SchoolModelAssignmentCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "settings:write", db)
    school = db.query(models.School).filter(models.School.id == payload.school_id).first()
    if not school or not school_context.user_can_access_school(db, current_user, school):
        raise HTTPException(status_code=403, detail="Etablissement non autorise.")
    organization, assignments, seeded = school_model_templates.ensure_school_foundation(
        db,
        school,
        owner_user_id=current_user.id if current_user.role == models.UserRole.SUPER_ADMIN else None,
        model_codes=payload.model_codes,
        seed_defaults=payload.seed_defaults,
    )
    audit.record_audit(
        db,
        action="school_models.assigned",
        current_user=current_user,
        entity_type="school",
        entity_id=school.id,
        details={"organization_id": organization.id, "model_codes": payload.model_codes, "seeded": seeded},
    )
    db.commit()
    return {"assignments": [_assignment_payload(row) for row in assignments], "seeded": seeded}


@router.patch("/assignments/{assignment_id}")
def update_assignment(
    assignment_id: int,
    payload: schemas.SchoolModelAssignmentUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "settings:write", db)
    assignment = db.query(models.SchoolModelAssignment).options(
        joinedload(models.SchoolModelAssignment.school),
        joinedload(models.SchoolModelAssignment.school_model),
    ).filter(models.SchoolModelAssignment.id == assignment_id).first()
    if not assignment or not school_context.user_can_access_school(db, current_user, assignment.school):
        raise HTTPException(status_code=404, detail="Affectation introuvable.")
    old = {
        "display_name": assignment.display_name,
        "is_active": assignment.is_active,
        "ai_enabled": assignment.ai_enabled,
        "monthly_ai_credit_limit": assignment.monthly_ai_credit_limit,
    }
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(assignment, key, value)
    audit.record_audit(
        db,
        action="school_model_assignment.updated",
        current_user=current_user,
        entity_type="school_model_assignment",
        entity_id=assignment.id,
        details={"old": old, "new": payload.model_dump(exclude_unset=True)},
    )
    db.commit()
    return _assignment_payload(assignment)
