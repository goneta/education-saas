"""Personnel scolaire (#7) — create and manage school staff accounts.

Creating a staff member auto-creates the underlying User account (with the
chosen primary role) and a StaffProfile carrying establishment, department,
function, additional roles and an operational status. School-scoped; managed by
School Admin / Super Admin.
"""

import secrets
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security

router = APIRouter(prefix="/personnel", tags=["Personnel"])

STAFF_STATUSES = {"active", "inactive", "suspended", "on_leave"}


def _ensure_admin(current_user: models.User) -> None:
    if current_user.role not in (models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Administrateur d'établissement uniquement.")


def _resolve_school(current_user: models.User, school_id: Optional[int]) -> int:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if not school_id:
            raise HTTPException(status_code=400, detail="school_id requis pour le Super Admin.")
        return school_id
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Contexte d'établissement requis.")
    return current_user.school_id


def _valid_role(value: str) -> models.UserRole:
    try:
        return models.UserRole(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Rôle inconnu : {value}")


def _serialize(profile: models.StaffProfile, user: models.User, department: Optional[models.Department] = None, generated_password: Optional[str] = None) -> schemas.StaffResponse:
    return schemas.StaffResponse(
        id=profile.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        primary_role=user.role.value if user.role else None,
        additional_roles=profile.additional_roles or [],
        department_id=profile.department_id,
        department_name=department.name if department else None,
        job_title=profile.job_title,
        status=profile.status,
        is_active=bool(user.is_active),
        generated_password=generated_password,
    )


@router.get("", response_model=List[schemas.StaffResponse])
@router.get("/", response_model=List[schemas.StaffResponse], include_in_schema=False)
def list_staff(school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _resolve_school(current_user, school_id)
    rows = (
        db.query(models.StaffProfile, models.User)
        .join(models.User, models.User.id == models.StaffProfile.user_id)
        .filter(models.StaffProfile.school_id == resolved)
        .order_by(models.User.full_name.asc())
        .all()
    )
    departments = {d.id: d for d in db.query(models.Department).filter(models.Department.school_id == resolved).all()}
    return [_serialize(p, u, departments.get(p.department_id)) for p, u in rows]


@router.post("", response_model=schemas.StaffResponse, status_code=201)
@router.post("/", response_model=schemas.StaffResponse, status_code=201, include_in_schema=False)
def create_staff(payload: schemas.StaffCreate, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _resolve_school(current_user, school_id)
    role = _valid_role(payload.primary_role)
    for extra in payload.additional_roles:
        _valid_role(extra)
    if db.query(models.User.id).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Un compte avec cet e-mail existe déjà.")
    if payload.department_id and not db.query(models.Department.id).filter(models.Department.id == payload.department_id, models.Department.school_id == resolved).first():
        raise HTTPException(status_code=404, detail="Département introuvable.")
    if payload.status not in STAFF_STATUSES:
        raise HTTPException(status_code=422, detail=f"Statut invalide : {payload.status}")

    generated = None
    raw_password = payload.password
    if not raw_password:
        generated = secrets.token_urlsafe(9)
        raw_password = generated

    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=security.get_password_hash(raw_password),
        role=role,
        school_id=resolved,
        phone_number=payload.phone_number,
        is_active=payload.status == "active",
        is_verified=False,
    )
    db.add(user)
    db.flush()
    profile = models.StaffProfile(
        user_id=user.id,
        school_id=resolved,
        department_id=payload.department_id,
        job_title=payload.job_title,
        additional_roles=payload.additional_roles or [],
        status=payload.status,
    )
    db.add(profile)
    audit.record_audit(db, action="personnel.staff.created", current_user=current_user, entity_type="staff_profile", entity_id=user.id)
    db.commit()
    db.refresh(profile)
    db.refresh(user)
    department = db.query(models.Department).filter(models.Department.id == profile.department_id).first() if profile.department_id else None
    return _serialize(profile, user, department, generated_password=generated)


@router.patch("/{staff_id}", response_model=schemas.StaffResponse)
def update_staff(staff_id: int, payload: schemas.StaffUpdate, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _resolve_school(current_user, school_id)
    profile = db.query(models.StaffProfile).filter(models.StaffProfile.id == staff_id, models.StaffProfile.school_id == resolved).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Membre du personnel introuvable.")
    user = db.query(models.User).filter(models.User.id == profile.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Compte utilisateur introuvable.")

    data = payload.model_dump(exclude_unset=True)
    if "primary_role" in data and data["primary_role"] is not None:
        user.role = _valid_role(data["primary_role"])
    if "additional_roles" in data and data["additional_roles"] is not None:
        for extra in data["additional_roles"]:
            _valid_role(extra)
        profile.additional_roles = data["additional_roles"]
    if "full_name" in data and data["full_name"] is not None:
        user.full_name = data["full_name"]
    if "phone_number" in data:
        user.phone_number = data["phone_number"]
    if "is_active" in data and data["is_active"] is not None:
        user.is_active = data["is_active"]
    if "department_id" in data:
        if data["department_id"] and not db.query(models.Department.id).filter(models.Department.id == data["department_id"], models.Department.school_id == resolved).first():
            raise HTTPException(status_code=404, detail="Département introuvable.")
        profile.department_id = data["department_id"]
    if "job_title" in data:
        profile.job_title = data["job_title"]
    if "status" in data and data["status"] is not None:
        if data["status"] not in STAFF_STATUSES:
            raise HTTPException(status_code=422, detail=f"Statut invalide : {data['status']}")
        profile.status = data["status"]

    audit.record_audit(db, action="personnel.staff.updated", current_user=current_user, entity_type="staff_profile", entity_id=profile.id)
    db.commit()
    db.refresh(profile)
    db.refresh(user)
    department = db.query(models.Department).filter(models.Department.id == profile.department_id).first() if profile.department_id else None
    return _serialize(profile, user, department)


@router.delete("/{staff_id}", status_code=204)
def delete_staff(staff_id: int, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Remove a staff profile and deactivate its user account (never hard-delete
    the user, which may carry historical records)."""
    _ensure_admin(current_user)
    resolved = _resolve_school(current_user, school_id)
    profile = db.query(models.StaffProfile).filter(models.StaffProfile.id == staff_id, models.StaffProfile.school_id == resolved).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Membre du personnel introuvable.")
    user = db.query(models.User).filter(models.User.id == profile.user_id).first()
    if user is not None:
        user.is_active = False
    db.delete(profile)
    audit.record_audit(db, action="personnel.staff.deleted", current_user=current_user, entity_type="staff_profile", entity_id=staff_id)
    db.commit()
