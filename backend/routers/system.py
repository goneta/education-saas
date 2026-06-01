from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from .. import localization, models, schemas, security, database, rbac

router = APIRouter(prefix="/system", tags=["System Configuration"])

SCHOOL_TEMPLATES = {
    "primary": {
        "classes": [("CP1", "CP1"), ("CP2", "CP2"), ("CE1", "CE1"), ("CE2", "CE2"), ("CM1", "CM1"), ("CM2", "CM2")],
        "subjects": ["Francais", "Mathematiques", "Sciences", "Histoire-Geographie", "Education civique"],
        "programs": [],
        "fees": [("Inscription", 25000, 1, True), ("Scolarite", 150000, 2, True), ("Assurance", 5000, 3, True)],
    },
    "secondary": {
        "classes": [("6eme", "6eme"), ("5eme", "5eme"), ("4eme", "4eme"), ("3eme", "3eme"), ("2nde", "2nde"), ("1ere", "1ere"), ("Terminale", "Terminale")],
        "subjects": ["Francais", "Mathematiques", "Physique-Chimie", "SVT", "Anglais", "Histoire-Geographie", "Philosophie"],
        "programs": [],
        "fees": [("Inscription", 35000, 1, True), ("Scolarite", 250000, 2, True), ("Assurance", 5000, 3, True), ("Examens", 15000, 4, False)],
    },
    "general": {
        "classes": [("6eme", "6eme"), ("5eme", "5eme"), ("4eme", "4eme"), ("3eme", "3eme"), ("2nde", "2nde"), ("1ere", "1ere"), ("Terminale", "Terminale")],
        "subjects": ["Francais", "Mathematiques", "Physique-Chimie", "SVT", "Anglais", "Histoire-Geographie"],
        "programs": [],
        "fees": [("Inscription", 35000, 1, True), ("Scolarite", 250000, 2, True), ("Assurance", 5000, 3, True)],
    },
    "technical": {
        "classes": [("2nde Technique", "2nde"), ("1ere Technique", "1ere"), ("Terminale Technique", "Terminale"), ("BTS 1", "BTS1"), ("BTS 2", "BTS2")],
        "subjects": ["Mathematiques appliquees", "Technologie", "Atelier", "Gestion", "Anglais technique"],
        "programs": [("Electrotechnique", "technique", "BTS", "BTS", 2), ("Maintenance industrielle", "technique", "BTS", "BTS", 2)],
        "fees": [("Inscription", 50000, 1, True), ("Scolarite", 400000, 2, True), ("Atelier", 60000, 3, True), ("Assurance", 10000, 4, True)],
    },
    "vocational": {
        "classes": [("CAP 1", "CAP1"), ("CAP 2", "CAP2"), ("BEP 1", "BEP1"), ("BEP 2", "BEP2")],
        "subjects": ["Pratique professionnelle", "Technologie", "Entrepreneuriat", "Francais professionnel"],
        "programs": [("Cuisine", "professionnel", "CAP", "CAP", 2), ("Mecanique", "professionnel", "CAP", "CAP", 2)],
        "fees": [("Inscription", 40000, 1, True), ("Scolarite", 300000, 2, True), ("Equipement", 50000, 3, True)],
    },
    "professional": {
        "classes": [("CAP 1", "CAP1"), ("CAP 2", "CAP2"), ("BTS Pro 1", "BTS1"), ("BTS Pro 2", "BTS2")],
        "subjects": ["Pratique professionnelle", "Gestion projet", "Stage", "Communication professionnelle"],
        "programs": [("Commerce", "professionnel", "BTS", "BTS", 2), ("Informatique de gestion", "professionnel", "BTS", "BTS", 2)],
        "fees": [("Inscription", 45000, 1, True), ("Scolarite", 350000, 2, True), ("Stage", 25000, 3, False)],
    },
    "university": {
        "classes": [("Licence 1", "L1"), ("Licence 2", "L2"), ("Licence 3", "L3"), ("Master 1", "M1"), ("Master 2", "M2")],
        "subjects": ["Methodologie", "Anglais", "Informatique", "Projet tutoré"],
        "programs": [("Licence Gestion", "universite", "Licence", "Licence", 3), ("Master Management", "universite", "Master", "Master", 2)],
        "fees": [("Inscription", 75000, 1, True), ("Credits pedagogiques", 500000, 2, True), ("Bibliotheque", 25000, 3, False)],
    },
}

# Schemas (Internal for now, can move to schemas.py later)
class ReferenceDataCreate(BaseModel):
    category: str
    key: str
    value: Dict[str, Any] # {"fr": "...", "en": "..."}
    order: int = 0
    school_id: Optional[int] = None # Optional override for specific school

class ReferenceDataUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None

class ReferenceDataResponse(ReferenceDataCreate):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class SchoolStatusUpdate(BaseModel):
    is_active: bool

class ApplyTemplateRequest(BaseModel):
    template: Optional[str] = None


def _school_settings_payload(school: models.School) -> dict:
    return {
        "id": school.id,
        "name": school.name,
        "domain_prefix": school.domain_prefix,
        "school_type": school.school_type,
        "address": school.address,
        "phone": school.phone,
        "email": school.email,
        "country_code": school.country_code,
        "default_currency": school.default_currency,
        "currency_code": school.currency_code,
        "primary_language": school.primary_language,
        "timezone": school.timezone,
        "date_format": school.date_format,
        "time_format": school.time_format,
        "address_structured": school.address_structured,
        "formatted_address": school.formatted_address,
        "phone_country_code": school.phone_country_code,
        "phone_e164": school.phone_e164,
        "is_active": school.is_active,
        "subscription_plan": school.subscription_plan,
        "subscription_status": school.subscription_status,
        "storage_quota_mb": school.storage_quota_mb,
        "current_billing_period_end": school.current_billing_period_end,
        "created_at": school.created_at,
        "localization_profile": localization.country_profile(school.country_code),
        "school_type_profile": localization.localized_school_type_profile(school.school_type.value, school.country_code),
    }

@router.post("/reference-data", response_model=ReferenceDataResponse)
def create_reference_data(
    data: ReferenceDataCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Only Global Admins or School Admins can manage this
    if current_user.role not in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN]:
         raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check uniqueness
    exists = db.query(models.ReferenceData).filter(
        models.ReferenceData.category == data.category,
        models.ReferenceData.key == data.key,
        models.ReferenceData.school_id == data.school_id # Scope check
    ).first()
    
    if exists:
        raise HTTPException(status_code=400, detail="Key already exists in this scope")

    new_ref = models.ReferenceData(
        category=data.category,
        key=data.key,
        value=data.value,
        order=data.order,
        school_id=data.school_id
    )
    db.add(new_ref)
    db.commit()
    db.refresh(new_ref)
    return new_ref

@router.get("/reference-data/{category}", response_model=List[ReferenceDataResponse])
def get_reference_data(
    category: str,
    school_id: Optional[int] = None, # If provided, fetches Global + School Specific
    db: Session = Depends(database.get_db)
):
    query = db.query(models.ReferenceData).filter(
        models.ReferenceData.category == category,
        models.ReferenceData.is_active == True
    )
    
    if school_id:
        # Fetch Global (school_id is Null) OR School Specific
        query = query.filter((models.ReferenceData.school_id == None) | (models.ReferenceData.school_id == school_id))
    else:
        # Default to Global only if no school specified?
        # Or maybe minimal set. For now, fetch Global.
        query = query.filter(models.ReferenceData.school_id == None)
        
    return query.order_by(models.ReferenceData.order).all()


@router.get("/localization/countries")
def list_country_profiles():
    return {
        "supported_currencies": sorted(localization.SUPPORTED_CURRENCIES),
        "supported_locales": sorted(localization.SUPPORTED_LOCALES),
        "countries": localization.COUNTRY_PROFILES,
    }


@router.get("/school-settings", response_model=schemas.SchoolSettingsResponse)
def get_school_settings(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    rbac.require_permission(current_user, "settings:read", db)
    school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return _school_settings_payload(school)


@router.put("/school-settings", response_model=schemas.SchoolSettingsResponse)
def update_school_settings(
    payload: schemas.SchoolSettingsUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    rbac.require_permission(current_user, "settings:write", db)
    school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    country_changed = bool(payload.country_code and payload.country_code != school.country_code)
    profile = localization.country_profile(payload.country_code or school.country_code)
    currency = payload.default_currency or (profile["currency"] if country_changed else school.default_currency) or profile["currency"]
    if currency not in localization.SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {currency}")
    language = payload.primary_language or (profile["locale"] if country_changed else school.primary_language) or profile["locale"]
    if language not in localization.SUPPORTED_LOCALES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    raw_phone = payload.phone if payload.phone is not None else school.phone
    phone_country = payload.phone_country_code or payload.country_code or school.phone_country_code or profile["country_code"]
    valid_phone, phone_e164, phone_error = localization.validate_phone(raw_phone, phone_country)
    if not valid_phone:
        raise HTTPException(status_code=400, detail=phone_error)

    for field in ["name", "school_type", "email", "website", "phone"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(school, field, value)
    school.country_code = profile["country_code"]
    school.default_currency = currency
    school.currency_code = payload.currency_code or (profile["currency_code"] if country_changed else school.currency_code) or profile["currency_code"]
    school.primary_language = language
    school.timezone = payload.timezone or (profile["timezone"] if country_changed else school.timezone) or profile["timezone"]
    school.date_format = payload.date_format or (profile["date_format"] if country_changed else school.date_format) or profile["date_format"]
    school.time_format = payload.time_format or (profile["time_format"] if country_changed else school.time_format) or profile["time_format"]
    school.phone_country_code = phone_country
    school.phone_e164 = phone_e164
    if payload.address_structured is not None:
        structured = payload.address_structured.model_dump()
        if not structured.get("country"):
            structured["country"] = profile["name"]
        structured["formatted"] = localization.format_address(structured)
        school.address_structured = structured
        school.formatted_address = structured["formatted"]
        school.address = structured["formatted"]

    db.commit()
    db.refresh(school)
    return _school_settings_payload(school)


@router.get("/schools", response_model=List[schemas.SchoolResponse])
def list_schools(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin only")
    schools = db.query(models.School).order_by(models.School.created_at.desc()).all()
    return [
        {
            "id": school.id,
            "name": school.name,
            "domain_prefix": school.domain_prefix,
            "school_type": school.school_type,
            "address": school.address,
            "is_active": school.is_active,
            "created_at": school.created_at,
        }
        for school in schools
    ]


@router.patch("/schools/{school_id}/status")
def update_school_status(
    school_id: int,
    status_update: SchoolStatusUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin only")
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    school.is_active = status_update.is_active
    db.commit()
    db.refresh(school)
    return {"id": school.id, "is_active": school.is_active}


@router.put("/schools/{school_id}/subscription")
def update_school_subscription(
    school_id: int,
    payload: schemas.SubscriptionSettingsUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin only")
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(school, field, value)
    school.is_active = school.subscription_status != "suspended"
    db.commit()
    db.refresh(school)
    return _school_settings_payload(school)


@router.get("/users", response_model=List[schemas.UserResponse])
def list_users(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.User)
    if current_user.role == models.UserRole.SUPER_ADMIN:
        pass
    elif current_user.role in [models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION]:
        query = query.filter(models.User.school_id == current_user.school_id)
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    return query.order_by(models.User.created_at.desc()).all()


@router.get("/permissions")
def my_permissions(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    return rbac.permission_snapshot(current_user, db)


@router.get("/permissions/catalog")
def permission_catalog(current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {
        "roles": [role.value for role in models.UserRole],
        "permissions": rbac.permission_catalog(),
        "defaults": {
            role.value: sorted(values)
            for role, values in rbac.PERMISSIONS.items()
        },
    }


@router.get("/role-permissions/{role}", response_model=schemas.RolePermissionResponse)
def get_role_permissions(
    role: models.UserRole,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role not in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION]:
        raise HTTPException(status_code=403, detail="Not authorized")
    school_id = None if current_user.role == models.UserRole.SUPER_ADMIN else current_user.school_id
    return rbac.role_permission_snapshot(role, school_id, db)


@router.put("/role-permissions/{role}", response_model=schemas.RolePermissionResponse)
def update_role_permissions(
    role: models.UserRole,
    payload: schemas.RolePermissionUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role not in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update role permissions")
    if role in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN] and current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can edit admin roles")

    available = set(rbac.permission_catalog())
    requested = set(payload.permissions)
    unknown = sorted(requested - available - {"*"})
    if unknown:
        raise HTTPException(status_code=400, detail={"unknown_permissions": unknown})

    school_id = None if current_user.role == models.UserRole.SUPER_ADMIN else current_user.school_id
    base = set(rbac.PERMISSIONS.get(role, set()))
    if "*" in base:
        base = set(available)
        base.add("*")

    existing = {
        row.permission: row
        for row in db.query(models.RolePermission).filter(
            models.RolePermission.role == role,
            models.RolePermission.school_id == school_id,
        ).all()
    }

    for permission in sorted((base | requested | set(existing)) - {"*"}):
        should_enable = permission in requested
        if permission in existing:
            existing[permission].is_enabled = should_enable
            existing[permission].updated_by_id = current_user.id
        else:
            db.add(models.RolePermission(
                role=role,
                permission=permission,
                is_enabled=should_enable,
                school_id=school_id,
                updated_by_id=current_user.id,
            ))
    db.commit()
    return rbac.role_permission_snapshot(role, school_id, db)


@router.get("/school-templates")
def list_school_templates():
    return {
        key: {
            "classes": [name for name, _level in value["classes"]],
            "subjects": value["subjects"],
            "programs": [program[0] for program in value["programs"]],
            "fees": [{"name": row[0], "amount": row[1], "order": row[2], "required": row[3]} for row in value["fees"]],
        }
        for key, value in SCHOOL_TEMPLATES.items()
    }


@router.post("/schools/{school_id}/apply-template")
def apply_school_template(
    school_id: int,
    payload: ApplyTemplateRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role == models.UserRole.SUPER_ADMIN:
        school = db.query(models.School).filter(models.School.id == school_id).first()
    elif current_user.role == models.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id:
        school = db.query(models.School).filter(models.School.id == school_id).first()
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    template_key = payload.template or school.school_type.value
    template = SCHOOL_TEMPLATES.get(template_key)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    created = {"classes": 0, "subjects": 0, "programs": 0, "fees": 0}
    for name, level in template["classes"]:
        exists = db.query(models.Class).filter(models.Class.school_id == school.id, models.Class.name == name).first()
        if not exists:
            db.add(models.Class(name=name, level=level, school_id=school.id))
            created["classes"] += 1
    for name in template["subjects"]:
        exists = db.query(models.Subject).filter(models.Subject.school_id == school.id, models.Subject.name == name).first()
        if not exists:
            db.add(models.Subject(name=name, code=name.upper().replace(" ", "_")[:20], school_id=school.id))
            created["subjects"] += 1
    for name, sector, level, diploma, duration in template["programs"]:
        exists = db.query(models.AcademicProgram).filter(models.AcademicProgram.school_id == school.id, models.AcademicProgram.name == name).first()
        if not exists:
            db.add(models.AcademicProgram(name=name, sector=sector, level=level, diploma=diploma, duration_years=duration, school_id=school.id))
            created["programs"] += 1
    for name, amount, order, required in template["fees"]:
        exists = db.query(models.FeeSchedule).filter(models.FeeSchedule.school_id == school.id, models.FeeSchedule.name == name, models.FeeSchedule.level == None, models.FeeSchedule.class_id == None).first()
        if not exists:
            db.add(models.FeeSchedule(name=name, amount=amount, category_order=order, is_required=required, is_current=True, school_id=school.id))
            created["fees"] += 1
    db.commit()
    return {"template": template_key, "created": created}


@router.post("/startup-wizard")
def startup_wizard(
    payload: schemas.StartupWizardRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    rbac.require_permission(current_user, "settings:write", db)
    school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    year = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school.id,
        models.AcademicYear.name == payload.academic_year_name,
    ).first()
    if not year:
        year = models.AcademicYear(
            name=payload.academic_year_name,
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_current=True,
            school_id=school.id,
        )
        db.add(year)
        db.flush()
    template_created = {}
    if payload.create_defaults:
        template_key = payload.template or school.school_type.value
        template = SCHOOL_TEMPLATES.get(template_key)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        template_created = {"classes": 0, "subjects": 0, "programs": 0, "fees": 0}
        for name, level in template["classes"]:
            if not db.query(models.Class).filter(models.Class.school_id == school.id, models.Class.name == name).first():
                db.add(models.Class(name=name, level=level, school_id=school.id))
                template_created["classes"] += 1
        for name in template["subjects"]:
            if not db.query(models.Subject).filter(models.Subject.school_id == school.id, models.Subject.name == name).first():
                db.add(models.Subject(name=name, code=name.upper().replace(" ", "_")[:20], school_id=school.id))
                template_created["subjects"] += 1
        for name, amount, order, required in template["fees"]:
            if not db.query(models.FeeSchedule).filter(models.FeeSchedule.school_id == school.id, models.FeeSchedule.name == name, models.FeeSchedule.academic_year_id == year.id).first():
                db.add(models.FeeSchedule(name=name, amount=amount, category_order=order, is_required=required, is_current=True, academic_year_id=year.id, school_id=school.id))
                template_created["fees"] += 1
    db.commit()
    return {"academic_year_id": year.id, "created": template_created}


@router.get("/audit-logs", response_model=List[schemas.AuditLogResponse])
def list_audit_logs(
    actor_id: Optional[int] = None,
    path: Optional[str] = None,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "audit:read", db)
    query = db.query(models.AuditLog)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.AuditLog.school_id == current_user.school_id)
    if actor_id:
        query = query.filter(models.AuditLog.actor_id == actor_id)
    if path:
        query = query.filter(models.AuditLog.path.like(f"%{path}%"))
    return query.order_by(models.AuditLog.created_at.desc()).limit(min(limit, 500)).all()


@router.get("/security-events", response_model=List[schemas.SecurityEventResponse])
def list_security_events(
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "security:read", db)
    query = db.query(models.SecurityEvent)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.SecurityEvent.school_id == current_user.school_id)
    if severity:
        query = query.filter(models.SecurityEvent.severity == severity)
    if event_type:
        query = query.filter(models.SecurityEvent.event_type == event_type)
    return query.order_by(models.SecurityEvent.created_at.desc()).limit(min(limit, 500)).all()


@router.get("/compliance/data-export", response_model=schemas.ComplianceExportResponse)
def compliance_data_export(
    user_id: Optional[int] = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "compliance:export", db)
    school_id = current_user.school_id if current_user.role != models.UserRole.SUPER_ADMIN else None
    user_query = db.query(models.User)
    if school_id:
        user_query = user_query.filter(models.User.school_id == school_id)
    if user_id:
        user_query = user_query.filter(models.User.id == user_id)
    users = user_query.all()
    payload = {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "school_id": user.school_id,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user in users
        ],
        "students": [],
        "teachers": [],
        "files": [],
    }
    for user in users:
        if user.student_profile:
            payload["students"].append({
                "user_id": user.id,
                "registration_number": user.student_profile.registration_number,
                "parent_name": user.student_profile.parent_name,
                "parent_phone_e164": user.student_profile.parent_phone_e164,
                "status": user.student_profile.status.value,
            })
        if user.teacher_profile:
            payload["teachers"].append({
                "user_id": user.id,
                "specialization": user.teacher_profile.specialization,
                "join_date": user.teacher_profile.join_date,
            })
    files_query = db.query(models.SecureFile)
    if school_id:
        files_query = files_query.filter(models.SecureFile.school_id == school_id)
    payload["files"] = [
        {
            "id": row.id,
            "original_filename": row.original_filename,
            "content_type": row.content_type,
            "size_bytes": row.size_bytes,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in files_query.limit(5000).all()
    ]
    return {
        "generated_at": datetime.utcnow(),
        "school_id": school_id,
        "user_id": user_id,
        "payload": payload,
    }


@router.post("/compliance/erase-user")
def compliance_erase_user(
    payload: schemas.ComplianceEraseRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "compliance:erase", db)
    query = db.query(models.User).filter(models.User.id == payload.user_id)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.User.school_id == current_user.school_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN] and current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can erase admin accounts")
    anonymized = f"anonymized-{user.id}@deleted.local"
    user.email = anonymized
    user.full_name = "Utilisateur anonymise"
    user.phone_number = None
    user.phone_e164 = None
    user.address = None
    user.address_structured = None
    user.formatted_address = None
    user.is_active = False
    user.token_version += 1
    if user.student_profile:
        user.student_profile.parent_name = "Anonymise"
        user.student_profile.parent_phone = "Anonymise"
        user.student_profile.parent_phone_e164 = None
        user.student_profile.parent_email = None
        user.student_profile.student_address = None
        user.student_profile.parent_address = None
    db.add(models.AuditLog(
        action="compliance.erase_user",
        entity_type="user",
        entity_id=str(user.id),
        details={"reason": payload.reason, "anonymize_only": payload.anonymize_only},
        actor_id=current_user.id,
        school_id=user.school_id,
    ))
    db.commit()
    return {"message": "User data anonymized", "user_id": user.id}


@router.get("/compliance/consents", response_model=List[schemas.DataConsentResponse])
def list_consents(
    subject_user_id: Optional[int] = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "compliance:export", db)
    query = db.query(models.DataConsent)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.DataConsent.school_id == current_user.school_id)
    if subject_user_id:
        query = query.filter(models.DataConsent.subject_user_id == subject_user_id)
    return query.order_by(models.DataConsent.recorded_at.desc()).limit(500).all()


@router.post("/compliance/consents", response_model=schemas.DataConsentResponse)
def record_consent(
    payload: schemas.DataConsentCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "compliance:export", db)
    subject = db.query(models.User).filter(models.User.id == payload.subject_user_id).first()
    if not subject or (current_user.role != models.UserRole.SUPER_ADMIN and subject.school_id != current_user.school_id):
        raise HTTPException(status_code=404, detail="Subject user not found")
    row = models.DataConsent(**payload.model_dump(), school_id=subject.school_id, recorded_by_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/compliance/retention-rules", response_model=List[schemas.DataRetentionRuleResponse])
def list_retention_rules(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    rbac.require_permission(current_user, "compliance:export", db)
    query = db.query(models.DataRetentionRule)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter((models.DataRetentionRule.school_id == current_user.school_id) | (models.DataRetentionRule.school_id == None))
    return query.order_by(models.DataRetentionRule.data_category.asc()).all()


@router.post("/compliance/retention-rules", response_model=schemas.DataRetentionRuleResponse)
def create_retention_rule(
    payload: schemas.DataRetentionRuleCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "compliance:erase", db)
    row = models.DataRetentionRule(
        **payload.model_dump(),
        school_id=None if current_user.role == models.UserRole.SUPER_ADMIN else current_user.school_id,
        created_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
