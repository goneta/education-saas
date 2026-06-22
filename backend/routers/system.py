from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from .. import audit, localization, models, schemas, security, database, rbac, tenancy
from ..services import ai_credits, file_storage, payment_gateway

router = APIRouter(prefix="/system", tags=["System Configuration"])

SCHOOL_SETTINGS_EDITABLE_FIELDS = {
    "name",
    "school_type",
    "email",
    "website",
    "phone",
    "logo_url",
    "registration_number",
}

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

TEMPLATE_REFERENCE_DEFAULTS = {
    "primary": {
        "diplomas": ["Certificat de fin de cycle primaire"],
        "semesters": ["Trimestre 1", "Trimestre 2", "Trimestre 3"],
        "certifications": ["Passage en classe superieure", "Assiduite"],
        "assessment_types": ["Devoir", "Composition", "Lecture", "Evaluation continue"],
    },
    "secondary": {
        "diplomas": ["BEPC", "Baccalaureat"],
        "semesters": ["Trimestre 1", "Trimestre 2", "Trimestre 3"],
        "certifications": ["BEPC", "Baccalaureat", "Attestation de scolarite"],
        "assessment_types": ["Interrogation", "Devoir surveille", "Composition", "Examen blanc"],
    },
    "general": {
        "diplomas": ["BEPC", "Baccalaureat general"],
        "semesters": ["Trimestre 1", "Trimestre 2", "Trimestre 3"],
        "certifications": ["BEPC", "Baccalaureat", "Attestation de scolarite"],
        "assessment_types": ["Interrogation", "Devoir surveille", "Composition", "Examen blanc"],
    },
    "technical": {
        "diplomas": ["BT", "BTS", "Certificat technique"],
        "semesters": ["Semestre 1", "Semestre 2", "Semestre 3", "Semestre 4"],
        "certifications": ["Certification atelier", "Attestation de stage", "BTS"],
        "assessment_types": ["Controle continu", "Pratique atelier", "Rapport de stage", "Examen final"],
    },
    "vocational": {
        "diplomas": ["CAP", "BEP", "Certificat professionnel"],
        "semesters": ["Session 1", "Session 2"],
        "certifications": ["Competence metier", "Attestation de stage", "Certification pratique"],
        "assessment_types": ["Evaluation pratique", "Competence", "Projet", "Examen final"],
    },
    "professional": {
        "diplomas": ["CAP", "BTS Pro", "Certificat professionnel"],
        "semesters": ["Session 1", "Session 2", "Session 3", "Session 4"],
        "certifications": ["Certification metier", "Attestation de stage", "Certification pratique"],
        "assessment_types": ["Evaluation pratique", "Competence", "Projet", "Rapport de stage"],
    },
    "university": {
        "diplomas": ["Licence", "Master", "Doctorat"],
        "semesters": ["Semestre 1", "Semestre 2", "Semestre 3", "Semestre 4", "Semestre 5", "Semestre 6"],
        "certifications": ["Releve certifie", "Diplome certifie", "Attestation ECTS"],
        "assessment_types": ["Controle continu", "Partiel", "Examen final", "Memoire", "Soutenance"],
    },
}


def _template_summary(template_key: str, template: dict) -> dict:
    references = TEMPLATE_REFERENCE_DEFAULTS.get(template_key, TEMPLATE_REFERENCE_DEFAULTS["primary"])
    levels = sorted({level for _name, level in template["classes"]})
    return {
        "classes": [name for name, _level in template["classes"]],
        "levels": levels,
        "subjects": template["subjects"],
        "programs": [program[0] for program in template["programs"]],
        "diplomas": references["diplomas"],
        "semesters": references["semesters"],
        "certifications": references["certifications"],
        "assessment_types": references["assessment_types"],
        "academic_years": [f"{datetime.utcnow().year}-{datetime.utcnow().year + 1}"],
        "fees": [{"name": row[0], "amount": row[1], "order": row[2], "required": row[3]} for row in template["fees"]],
    }


def _upsert_reference_data(db: Session, school_id: int, category: str, values: list[str]) -> int:
    created = 0
    for order, value in enumerate(values, start=1):
        key = value.lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        exists = db.query(models.ReferenceData).filter(
            models.ReferenceData.school_id == school_id,
            models.ReferenceData.category == category,
            models.ReferenceData.key == key,
        ).first()
        if not exists:
            db.add(models.ReferenceData(
                category=category,
                key=key,
                value={"fr": value, "en": value, "es": value, "sw": value},
                order=order,
                school_id=school_id,
            ))
            created += 1
    return created

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


class RoleDefinitionCreate(BaseModel):
    key: Optional[str] = None
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    color: str = "#0F766E"
    parent_role_key: Optional[str] = None
    permissions: List[str] = []


class RoleDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    parent_role_key: Optional[str] = None


class RoleDuplicateRequest(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    color: str = "#0F766E"


class RolePermissionMatrixUpdate(BaseModel):
    permissions: List[str]


class UserAdminCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: models.UserRole = models.UserRole.STAFF
    role_keys: List[str] = []
    school_id: Optional[int] = None
    phone_number: Optional[str] = None


class UserAdminUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[models.UserRole] = None
    is_active: Optional[bool] = None
    phone_number: Optional[str] = None
    role_keys: Optional[List[str]] = None
    school_id: Optional[int] = None


class PasswordResetRequest(BaseModel):
    new_password: str


class UserRolesUpdate(BaseModel):
    role_keys: List[str]


def _slugify_role_key(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")


def _rbac_school_id(current_user: models.User) -> Optional[int]:
    return None if current_user.role == models.UserRole.SUPER_ADMIN else current_user.school_id


def _assert_role_admin(current_user: models.User, db: Session) -> None:
    rbac.require_permission(current_user, "roles:manage_settings", db)


def _assert_user_admin(current_user: models.User, db: Session) -> None:
    rbac.require_permission(current_user, "users:manage_settings", db)


def _role_definition_payload(role: models.RoleDefinition, db: Session, assignment_school_id: Optional[int] = None) -> dict:
    users_count = db.query(models.UserRoleAssignment).join(
        models.User,
        models.User.id == models.UserRoleAssignment.user_id,
    ).filter(
        models.UserRoleAssignment.role_key == role.key,
        models.UserRoleAssignment.school_id == (assignment_school_id if assignment_school_id is not None else role.school_id),
        models.User.deleted_at == None,
    ).count()
    return {
        "id": role.id,
        "key": role.key,
        "name": role.name,
        "category": role.category,
        "description": role.description,
        "color": role.color,
        "is_system": role.is_system,
        "is_active": role.is_active,
        "parent_role_key": role.parent_role_key,
        "school_id": role.school_id,
        "users_count": users_count,
    }


def _ensure_default_roles(db: Session, school_id: Optional[int] = None) -> None:
    for role in rbac.default_role_definitions():
        exists = db.query(models.RoleDefinition).filter(
            models.RoleDefinition.key == role["key"],
            models.RoleDefinition.school_id == None,
        ).first()
        if not exists:
            db.add(models.RoleDefinition(**role, school_id=None))
    db.flush()


def _dedupe_role_rows(roles: List[models.RoleDefinition], school_id: Optional[int]) -> List[models.RoleDefinition]:
    selected: Dict[str, models.RoleDefinition] = {}
    for role in roles:
        current = selected.get(role.key)
        if current is None or (school_id is not None and role.school_id == school_id and current.school_id is None):
            selected[role.key] = role
    return sorted(selected.values(), key=lambda row: ((row.category or ""), row.name.lower(), row.key))


def _assign_user_roles(db: Session, user: models.User, role_keys: List[str], current_user: models.User) -> None:
    scoped_role_keys = sorted(set(role_keys + [user.role.value]))
    existing = {
        row.role_key: row
        for row in db.query(models.UserRoleAssignment).filter(
            models.UserRoleAssignment.user_id == user.id,
            models.UserRoleAssignment.school_id == user.school_id,
        ).all()
    }
    for key, row in list(existing.items()):
        if key not in scoped_role_keys:
            db.delete(row)
    for key in scoped_role_keys:
        if key not in existing:
            db.add(models.UserRoleAssignment(
                user_id=user.id,
                role_key=key,
                school_id=user.school_id,
                assigned_by_id=current_user.id,
            ))


def _school_settings_payload(school: models.School) -> dict:
    return {
        "id": school.id,
        "name": school.name,
        "domain_prefix": school.domain_prefix,
        "school_type": school.school_type,
        "address": school.address,
        "phone": school.phone,
        "email": school.email,
        "website": school.website,
        "logo_url": school.logo_url,
        "registration_number": school.registration_number,
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


SUBSCRIPTION_PRICES = {
    "free": {"monthly": 0, "yearly": 0},
    "pro": {"monthly": 99000, "yearly": 900000},
    "max": {"monthly": 199000, "yearly": 1700000},
}


def _current_subscription(db: Session, school_id: int) -> Optional[models.SchoolSubscription]:
    return db.query(models.SchoolSubscription).filter(
        models.SchoolSubscription.school_id == school_id,
    ).order_by(models.SchoolSubscription.created_at.desc(), models.SchoolSubscription.id.desc()).first()


def _managed_user_payload(db: Session, user: models.User) -> dict:
    assignments = db.query(models.UserRoleAssignment.role_key).filter(
        models.UserRoleAssignment.user_id == user.id,
        models.UserRoleAssignment.school_id == user.school_id,
    ).all()
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "role_keys": sorted({row[0] for row in assignments} | {user.role.value}),
        "phone_number": user.phone_number,
        "is_active": user.is_active,
        "school_id": user.school_id,
        "deleted_at": user.deleted_at,
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
    if payload.name is not None and not payload.name.strip():
        raise HTTPException(status_code=400, detail="School name is required")
    registration_number = payload.registration_number.strip() if payload.registration_number else None
    if registration_number:
        existing = db.query(models.School).filter(
            models.School.registration_number == registration_number,
            models.School.id != school.id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="School registration number already exists")

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

    for field in SCHOOL_SETTINGS_EDITABLE_FIELDS:
        value = getattr(payload, field)
        if value is not None:
            if isinstance(value, str):
                value = value.strip()
            if field == "registration_number" and value == "":
                value = None
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

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="School settings conflict with an existing record") from exc
    db.refresh(school)
    return _school_settings_payload(school)


@router.post("/school-settings/logo", response_model=schemas.SchoolSettingsResponse)
async def upload_school_logo(
    logo: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    rbac.require_permission(current_user, "settings:write", db)
    school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    if logo.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Le logo doit être une image PNG, JPEG ou WebP")
    metadata = await file_storage.store_upload(
        logo,
        school.id,
        document_name=f"Logo {school.name}",
        user_id=current_user.id,
        folder="branding",
    )
    row = models.SecureFile(
        **metadata,
        category="school_logo",
        visibility="public_internal",
        is_shareable=False,
        approval_status="approved",
        approved_by_id=current_user.id,
        approved_at=datetime.now(timezone.utc),
        entity_type="school_logo",
        entity_id=str(school.id),
        school_id=school.id,
        uploaded_by_id=current_user.id,
    )
    db.add(row)
    db.flush()
    school.logo_url = f"/system/schools/{school.id}/logo"
    audit.record_audit(
        db,
        action="school.logo.updated",
        current_user=current_user,
        entity_type="school",
        entity_id=school.id,
        details={"file_id": row.id, "content_type": row.content_type},
    )
    db.commit()
    db.refresh(school)
    return _school_settings_payload(school)


@router.get("/schools/{school_id}/logo")
def public_school_logo(school_id: int, db: Session = Depends(database.get_db)):
    row = db.query(models.SecureFile).filter(
        models.SecureFile.school_id == school_id,
        models.SecureFile.entity_type == "school_logo",
        models.SecureFile.entity_id == str(school_id),
        models.SecureFile.status == "active",
    ).order_by(models.SecureFile.created_at.desc(), models.SecureFile.id.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="Logo not found")
    if row.storage_backend in {"s3", "minio"}:
        url = file_storage.signed_download_url(row.storage_backend, row.storage_path, row.content_type, row.original_filename)
        if url:
            return RedirectResponse(url)
    return FileResponse(file_storage.open_stored_file(row.storage_path), media_type=row.content_type)


@router.get("/subscription", response_model=Optional[schemas.SchoolSubscriptionResponse])
def get_current_subscription(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    rbac.require_permission(current_user, "settings:read", db)
    return _current_subscription(db, current_user.school_id)


@router.post("/subscription/change")
def change_subscription(
    payload: schemas.SchoolSubscriptionChange,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    rbac.require_permission(current_user, "settings:write", db)
    school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    amount = float(SUBSCRIPTION_PRICES[payload.plan][payload.billing_cycle])
    now = datetime.now(timezone.utc)
    next_renewal = now + (timedelta(days=365) if payload.billing_cycle == "yearly" else timedelta(days=30))
    status_value = "active" if payload.plan == "free" else "pending_payment"
    payment_reference = None
    checkout_url = None
    provider_status = status_value
    if payload.plan != "free":
        provider = payload.payment_provider or "manual"
        payment_reference = ai_credits.platform_payment_reference("SUB")
        payment = models.PlatformPayment(
            reference=payment_reference,
            payer_user_id=current_user.id,
            school_id=school.id,
            payment_type="subscription",
            amount=amount,
            currency=school.default_currency or "FCFA",
            country_code=school.country_code,
            provider=provider,
            status="pending_payment",
            beneficiary_entity=ai_credits.beneficiary_for_region(school.country_code, None),
            credits_amount=0,
            metadata_json={"plan": payload.plan, "billing_cycle": payload.billing_cycle},
        )
        db.add(payment)
        db.flush()
        if provider in {"stripe", "djamo", "cinetpay"}:
            checkout = payment_gateway.create_checkout_session(
                provider=provider,
                reference=payment.reference,
                amount=payment.amount,
                currency=payment.currency,
                title=f"Abonnement TeducAI {payload.plan.upper()}",
            )
            payment.provider_reference = checkout.provider_reference
            payment.status = checkout.status
            checkout_url = checkout.checkout_url
            provider_status = checkout.status
    subscription = models.SchoolSubscription(
        school_id=school.id,
        plan=payload.plan,
        billing_cycle=payload.billing_cycle,
        amount=amount,
        currency=school.default_currency or "FCFA",
        status=status_value,
        started_at=now if payload.plan == "free" else None,
        next_renewal_at=next_renewal if payload.plan == "free" else None,
        expires_at=next_renewal if payload.plan == "free" else None,
        payment_provider=payload.payment_provider,
        payment_reference=payment_reference,
        created_by_id=current_user.id,
    )
    db.add(subscription)
    school.subscription_plan = payload.plan
    school.subscription_status = status_value
    school.current_billing_period_end = next_renewal if payload.plan == "free" else None
    audit.record_audit(
        db,
        action="school.subscription.changed",
        current_user=current_user,
        entity_type="school_subscription",
        details={
            "plan": payload.plan,
            "billing_cycle": payload.billing_cycle,
            "status": status_value,
            "payment_reference": payment_reference,
        },
    )
    db.commit()
    db.refresh(subscription)
    return {
        "subscription": schemas.SchoolSubscriptionResponse.model_validate(subscription),
        "checkout_url": checkout_url,
        "provider_status": provider_status,
    }


@router.get("/schools", response_model=List[schemas.SchoolResponse])
def list_schools(
    include_inactive: bool = True,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.School)
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if not include_inactive:
            query = query.filter(models.School.is_active == True)  # noqa: E712
    elif current_user.school_id:
        query = query.filter(models.School.id == current_user.school_id)
    else:
        raise HTTPException(status_code=400, detail="Vous devez d'abord créer ou être associé à un établissement scolaire.")
    return query.order_by(models.School.created_at.desc()).all()


@router.post("/schools", response_model=schemas.SchoolSettingsResponse)
def create_school(
    payload: schemas.SchoolCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin only")
    if db.query(models.School).filter(models.School.domain_prefix == payload.domain_prefix).first():
        raise HTTPException(status_code=400, detail="School domain already taken")
    country_profile = localization.country_profile(payload.country_code)
    address_structured = payload.address_structured.model_dump() if payload.address_structured else None
    school = models.School(
        name=payload.name,
        domain_prefix=payload.domain_prefix,
        school_type=payload.school_type,
        address=payload.address,
        phone=payload.phone,
        email=payload.email,
        website=payload.website,
        logo_url=payload.logo_url,
        registration_number=payload.registration_number,
        country_code=country_profile["country_code"],
        default_currency=payload.default_currency or country_profile["currency"],
        currency_code=payload.currency_code or country_profile["currency_code"],
        primary_language=payload.primary_language or country_profile["locale"],
        timezone=payload.timezone or country_profile["timezone"],
        date_format=payload.date_format or country_profile["date_format"],
        time_format=payload.time_format or country_profile["time_format"],
        address_structured=address_structured,
        formatted_address=localization.format_address(address_structured) or payload.address,
        phone_country_code=payload.phone_country_code or country_profile["country_code"],
    )
    db.add(school)
    db.flush()
    audit.record_audit(db, action="school.created", current_user=current_user, entity_type="school", entity_id=school.id)
    db.commit()
    db.refresh(school)
    return _school_settings_payload(school)


@router.get("/schools/{school_id}", response_model=schemas.SchoolSettingsResponse)
def get_school(
    school_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role != models.UserRole.SUPER_ADMIN and current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return _school_settings_payload(school)


@router.put("/schools/{school_id}", response_model=schemas.SchoolSettingsResponse)
def update_school(
    school_id: int,
    payload: schemas.SchoolSettingsUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role != models.UserRole.SUPER_ADMIN and current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "address_structured" and value is not None:
            value = value.model_dump() if hasattr(value, "model_dump") else value
            school.formatted_address = localization.format_address(value)
        setattr(school, field, value)
    audit.record_audit(db, action="school.updated", current_user=current_user, entity_type="school", entity_id=school.id)
    db.commit()
    db.refresh(school)
    return _school_settings_payload(school)


@router.delete("/schools/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin only")
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    school.is_active = False
    audit.record_audit(db, action="school.deleted_soft", current_user=current_user, entity_type="school", entity_id=school.id)
    db.commit()


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
    updates = payload.model_dump(exclude_unset=True)
    target_plan = updates.get("subscription_plan", school.subscription_plan or "free")
    target_status = updates.get("subscription_status", school.subscription_status or "active")
    if target_plan in {"pro", "max"} and target_status == "active":
        successful_payment = db.query(models.PlatformPayment.id).filter(
            models.PlatformPayment.school_id == school.id,
            models.PlatformPayment.payment_type == "subscription",
            models.PlatformPayment.status == "successful",
        ).first()
        if not successful_payment:
            raise HTTPException(
                status_code=409,
                detail="Un abonnement payant ne peut pas être activé sans paiement confirmé.",
            )
    for field, value in updates.items():
        if value is not None:
            setattr(school, field, value)
    school.is_active = school.subscription_status != "suspended"
    db.commit()
    db.refresh(school)
    return _school_settings_payload(school)


@router.get("/users")
def list_users(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.User).filter(models.User.deleted_at == None)
    if current_user.role == models.UserRole.SUPER_ADMIN:
        pass
    elif current_user.role in [models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION]:
        query = query.filter(models.User.school_id == current_user.school_id)
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    return [_managed_user_payload(db, row) for row in query.order_by(models.User.created_at.desc()).all()]


@router.get("/users/{user_id}")
def get_managed_user(
    user_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_user_admin(current_user, db)
    query = db.query(models.User).filter(models.User.id == user_id, models.User.deleted_at == None)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.User.school_id == current_user.school_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _managed_user_payload(db, user)


@router.get("/users/{user_id}/school-memberships", response_model=List[schemas.SchoolMembershipResponse])
def list_user_school_memberships(
    user_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.SchoolMembership).filter(models.SchoolMembership.user_id == user_id)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        if not current_user.school_id:
            raise HTTPException(status_code=400, detail=tenancy.SCHOOL_REQUIRED_MESSAGE)
        query = query.filter(models.SchoolMembership.school_id == current_user.school_id)
    rows = query.order_by(
        models.SchoolMembership.start_date.desc().nullslast(),
        models.SchoolMembership.created_at.desc(),
    ).all()
    if current_user.role != models.UserRole.SUPER_ADMIN and not rows:
        raise HTTPException(status_code=404, detail="Historique introuvable pour cette école")
    return rows


@router.post("/users", response_model=schemas.UserResponse)
def create_user_admin(
    payload: UserAdminCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_user_admin(current_user, db)
    security.validate_password_strength(payload.password)
    school_id = None if payload.role == models.UserRole.SUPER_ADMIN else (payload.school_id if current_user.role == models.UserRole.SUPER_ADMIN else current_user.school_id)
    if not school_id and payload.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="School context is required")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    if payload.role in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN] and current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can create admin accounts")
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=security.get_password_hash(payload.password),
        role=payload.role,
        school_id=school_id,
        phone_number=payload.phone_number,
        is_active=True,
    )
    db.add(user)
    db.flush()
    _assign_user_roles(db, user, payload.role_keys, current_user)
    audit.record_audit(db, action="rbac.user.created", current_user=current_user, entity_type="user", entity_id=user.id, details={"email": user.email, "roles": payload.role_keys})
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user_admin(
    user_id: int,
    payload: UserAdminUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_user_admin(current_user, db)
    query = db.query(models.User).filter(models.User.id == user_id, models.User.deleted_at == None)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.User.school_id == current_user.school_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_school_id = user.school_id
    old = {"email": user.email, "full_name": user.full_name, "role": user.role.value, "is_active": user.is_active}
    if payload.email is not None:
        duplicate = db.query(models.User).filter(models.User.email == payload.email, models.User.id != user.id).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = payload.email
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number
    if payload.role is not None:
        if payload.role in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN] and current_user.role != models.UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Only super admin can assign admin roles")
        user.role = payload.role
        if payload.role == models.UserRole.SUPER_ADMIN:
            user.school_id = None
    if "school_id" in payload.model_fields_set:
        if current_user.role != models.UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Only super admin can change a user's school")
        if payload.school_id is not None and not db.query(models.School.id).filter(models.School.id == payload.school_id).first():
            raise HTTPException(status_code=404, detail="School not found")
        if user.role != models.UserRole.SUPER_ADMIN:
            user.school_id = payload.school_id
    if payload.is_active is not None:
        user.is_active = payload.is_active
        user.token_version += 1
    if user.school_id != old_school_id:
        db.query(models.UserRoleAssignment).filter(models.UserRoleAssignment.user_id == user.id).delete()
    if payload.role_keys is not None:
        _assign_user_roles(db, user, payload.role_keys, current_user)
    elif user.school_id != old_school_id:
        _assign_user_roles(db, user, [], current_user)
    audit.record_audit(
        db,
        action="rbac.user.updated",
        current_user=current_user,
        entity_type="user",
        entity_id=user.id,
        details={"old": old, "new": {"email": user.email, "full_name": user.full_name, "role": user.role.value, "is_active": user.is_active, "roles": payload.role_keys}},
    )
    db.commit()
    db.refresh(user)
    return _managed_user_payload(db, user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_admin(
    user_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_user_admin(current_user, db)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    query = db.query(models.User).filter(models.User.id == user_id, models.User.deleted_at == None)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.User.school_id == current_user.school_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN] and current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can delete admin accounts")
    audit.record_audit(db, action="rbac.user.deleted_soft", current_user=current_user, entity_type="user", entity_id=user.id, details={"email": user.email})
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    user.token_version += 1
    db.commit()


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: PasswordResetRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_user_admin(current_user, db)
    security.validate_password_strength(payload.new_password)
    query = db.query(models.User).filter(models.User.id == user_id)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.User.school_id == current_user.school_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = security.get_password_hash(payload.new_password)
    user.token_version += 1
    audit.record_audit(db, action="rbac.user.password_reset", current_user=current_user, entity_type="user", entity_id=user.id)
    db.commit()
    return {"message": "Password reset", "user_id": user.id}


@router.get("/users/{user_id}/actions", response_model=List[schemas.AuditLogResponse])
def user_action_history(
    user_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "audit:view", db)
    query = db.query(models.AuditLog).filter(models.AuditLog.actor_id == user_id)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.AuditLog.school_id == current_user.school_id)
    return query.order_by(models.AuditLog.created_at.desc()).limit(200).all()


@router.put("/users/{user_id}/roles")
def assign_user_roles(
    user_id: int,
    payload: UserRolesUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_user_admin(current_user, db)
    query = db.query(models.User).filter(models.User.id == user_id)
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.User.school_id == current_user.school_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old = [row.role_key for row in db.query(models.UserRoleAssignment).filter(models.UserRoleAssignment.user_id == user.id).all()]
    _assign_user_roles(db, user, payload.role_keys, current_user)
    audit.record_audit(db, action="rbac.user.roles_assigned", current_user=current_user, entity_type="user", entity_id=user.id, details={"old": old, "new": payload.role_keys})
    db.commit()
    return {"user_id": user.id, "role_keys": sorted(set(payload.role_keys + [user.role.value]))}


@router.get("/permissions")
def my_permissions(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    return rbac.permission_snapshot(current_user, db)


@router.get("/active-context")
def active_context(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    snapshot = rbac.permission_snapshot(current_user, db)
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
            "school_id": current_user.school_id,
        },
        "roles": snapshot.get("roles", [current_user.role.value]),
        "active_role": current_user.role.value,
        "permissions": snapshot.get("permissions", []),
    }


@router.get("/permissions/catalog")
def permission_catalog(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role not in [models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION]:
        raise HTTPException(status_code=403, detail="Not authorized")
    school_id = _rbac_school_id(current_user)
    _ensure_default_roles(db, school_id)
    db.commit()
    roles = db.query(models.RoleDefinition).filter(
        (models.RoleDefinition.school_id == school_id) | (models.RoleDefinition.school_id == None)
    ).order_by(models.RoleDefinition.category.asc(), models.RoleDefinition.name.asc()).all()
    roles = _dedupe_role_rows(roles, school_id)
    return {
        "roles": list(dict.fromkeys(role.key for role in roles)),
        "role_definitions": [_role_definition_payload(role, db, school_id) for role in roles],
        "modules": rbac.permission_modules(),
        "actions": rbac.STANDARD_ACTIONS,
        "custom_role_examples": rbac.CUSTOM_ROLE_EXAMPLES,
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


@router.get("/role-management/roles")
def list_role_definitions(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_role_admin(current_user, db)
    school_id = _rbac_school_id(current_user)
    _ensure_default_roles(db, school_id)
    db.commit()
    roles = db.query(models.RoleDefinition).filter(
        (models.RoleDefinition.school_id == school_id) | (models.RoleDefinition.school_id == None)
    ).order_by(models.RoleDefinition.category.asc(), models.RoleDefinition.name.asc()).all()
    roles = _dedupe_role_rows(roles, school_id)
    return [_role_definition_payload(role, db, school_id) for role in roles]


@router.post("/role-management/roles")
def create_role_definition(
    payload: RoleDefinitionCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_role_admin(current_user, db)
    school_id = _rbac_school_id(current_user)
    key = payload.key or _slugify_role_key(payload.name)
    if not key:
        raise HTTPException(status_code=400, detail="Role key is required")
    if db.query(models.RoleDefinition).filter(models.RoleDefinition.key == key, models.RoleDefinition.school_id == school_id).first():
        raise HTTPException(status_code=400, detail="Role already exists")
    role = models.RoleDefinition(
        key=key,
        name=payload.name,
        category=payload.category or "Roles personnalises",
        description=payload.description,
        color=payload.color,
        is_system=False,
        is_active=True,
        parent_role_key=payload.parent_role_key,
        school_id=school_id,
        created_by_id=current_user.id,
    )
    db.add(role)
    db.flush()
    inherited = []
    if payload.parent_role_key:
        parent = rbac.role_key_permission_snapshot(payload.parent_role_key, school_id, db)
        inherited = parent["enabled_permissions"]
    for permission in sorted(set(inherited + payload.permissions)):
        if permission not in rbac.permission_catalog() and permission != "*":
            raise HTTPException(status_code=400, detail=f"Unknown permission: {permission}")
        if permission == "*":
            continue
        module, action = permission.split(":", 1)
        db.add(models.RolePermissionMatrix(
            role_key=key,
            module=module,
            action=action,
            permission=permission,
            is_enabled=True,
            school_id=school_id,
            updated_by_id=current_user.id,
        ))
    audit.record_audit(db, action="rbac.role.created", current_user=current_user, entity_type="role", entity_id=key, details=payload.model_dump())
    db.commit()
    db.refresh(role)
    return _role_definition_payload(role, db)


@router.put("/role-management/roles/{role_key}")
def update_role_definition(
    role_key: str,
    payload: RoleDefinitionUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_role_admin(current_user, db)
    school_id = _rbac_school_id(current_user)
    role = db.query(models.RoleDefinition).filter(models.RoleDefinition.key == role_key, models.RoleDefinition.school_id == school_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    old = _role_definition_payload(role, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    audit.record_audit(db, action="rbac.role.updated", current_user=current_user, entity_type="role", entity_id=role.key, details={"old": old, "new": payload.model_dump(exclude_unset=True)})
    db.commit()
    db.refresh(role)
    return _role_definition_payload(role, db)


@router.delete("/role-management/roles/{role_key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role_definition(
    role_key: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_role_admin(current_user, db)
    school_id = _rbac_school_id(current_user)
    role = db.query(models.RoleDefinition).filter(models.RoleDefinition.key == role_key, models.RoleDefinition.school_id == school_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="System roles cannot be deleted")
    db.query(models.UserRoleAssignment).filter(models.UserRoleAssignment.role_key == role_key, models.UserRoleAssignment.school_id == school_id).delete()
    db.query(models.RolePermissionMatrix).filter(models.RolePermissionMatrix.role_key == role_key, models.RolePermissionMatrix.school_id == school_id).delete()
    audit.record_audit(db, action="rbac.role.deleted", current_user=current_user, entity_type="role", entity_id=role.key, details={"name": role.name})
    db.delete(role)
    db.commit()


@router.post("/role-management/roles/{role_key}/duplicate")
def duplicate_role_definition(
    role_key: str,
    payload: RoleDuplicateRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    source = rbac.role_key_permission_snapshot(role_key, _rbac_school_id(current_user), db)
    return create_role_definition(
        RoleDefinitionCreate(
            key=payload.key,
            name=payload.name,
            category="Roles personnalises",
            description=payload.description,
            color=payload.color,
            parent_role_key=role_key,
            permissions=source["enabled_permissions"],
        ),
        current_user,
        db,
    )


@router.get("/role-management/roles/{role_key}/permissions")
def get_role_matrix_permissions(
    role_key: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_role_admin(current_user, db)
    school_id = _rbac_school_id(current_user)
    return rbac.role_key_permission_snapshot(role_key, school_id, db) | {
        "modules": rbac.permission_modules(),
        "actions": rbac.STANDARD_ACTIONS,
    }


@router.put("/role-management/roles/{role_key}/permissions")
def update_role_matrix_permissions(
    role_key: str,
    payload: RolePermissionMatrixUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_role_admin(current_user, db)
    school_id = _rbac_school_id(current_user)
    available = set(rbac.permission_catalog())
    requested = set(payload.permissions)
    unknown = sorted(requested - available - {"*"})
    if unknown:
        raise HTTPException(status_code=400, detail={"unknown_permissions": unknown})
    old = rbac.role_key_permission_snapshot(role_key, school_id, db)["enabled_permissions"]
    existing = {
        row.permission: row
        for row in db.query(models.RolePermissionMatrix).filter(
            models.RolePermissionMatrix.role_key == role_key,
            models.RolePermissionMatrix.school_id == school_id,
        ).all()
    }
    for permission in sorted((available | requested | set(existing)) - {"*"}):
        module, action = permission.split(":", 1)
        should_enable = permission in requested
        if permission in existing:
            existing[permission].is_enabled = should_enable
            existing[permission].updated_by_id = current_user.id
        else:
            db.add(models.RolePermissionMatrix(
                role_key=role_key,
                module=module,
                action=action,
                permission=permission,
                is_enabled=should_enable,
                school_id=school_id,
                updated_by_id=current_user.id,
            ))
    audit.record_audit(db, action="rbac.role.permissions_updated", current_user=current_user, entity_type="role", entity_id=role_key, details={"old": old, "new": sorted(requested)})
    db.commit()
    return rbac.role_key_permission_snapshot(role_key, school_id, db)


@router.get("/role-management/roles/{role_key}/users")
def list_role_users(
    role_key: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _assert_role_admin(current_user, db)
    school_id = _rbac_school_id(current_user)
    assignments = db.query(models.UserRoleAssignment).filter(
        models.UserRoleAssignment.role_key == role_key,
        models.UserRoleAssignment.school_id == school_id,
    ).all()
    user_ids = [row.user_id for row in assignments]
    users = db.query(models.User).filter(
        models.User.id.in_(user_ids),
        models.User.deleted_at == None,
    ).all() if user_ids else []
    return [{"id": user.id, "email": user.email, "full_name": user.full_name, "is_active": user.is_active, "role": user.role.value} for user in users]


@router.get("/school-templates")
def list_school_templates():
    return {
        key: _template_summary(key, value)
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

    summary = _template_summary(template_key, template)
    created = {"academic_years": 0, "classes": 0, "subjects": 0, "programs": 0, "fees": 0, "reference_data": 0, "semesters": 0}
    current_year_name = summary["academic_years"][0]
    current_year = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school.id,
        models.AcademicYear.name == current_year_name,
    ).first()
    if not current_year:
        year = datetime.utcnow().year
        current_year = models.AcademicYear(
            name=current_year_name,
            start_date=datetime(year, 9, 1),
            end_date=datetime(year + 1, 7, 31),
            is_current=True,
            school_id=school.id,
        )
        db.add(current_year)
        db.flush()
        created["academic_years"] += 1
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
            db.add(models.FeeSchedule(name=name, amount=amount, category_order=order, is_required=required, is_current=True, academic_year_id=current_year.id, school_id=school.id))
            created["fees"] += 1
    for order, name in enumerate(summary["semesters"], start=1):
        code = f"S{order}"
        exists = db.query(models.Semester).filter(models.Semester.school_id == school.id, models.Semester.name == name).first()
        if not exists:
            db.add(models.Semester(name=name, code=code, academic_year_id=current_year.id, school_id=school.id))
            created["semesters"] += 1
    for category in ["levels", "diplomas", "certifications", "assessment_types"]:
        created["reference_data"] += _upsert_reference_data(db, school.id, category, summary[category])
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
