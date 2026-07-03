"""Personnel scolaire (#7) — create and manage school staff accounts.

Creating a staff member auto-creates the underlying User account (with the
chosen primary role) and a StaffProfile carrying establishment, department,
function, additional roles and an operational status. School-scoped; managed by
School Admin / Super Admin.
"""

import secrets
from datetime import datetime
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
        # Policy-compliant random credential (length, cases, digit, special).
        generated = f"Tk{secrets.token_urlsafe(9)}!3a"
        raw_password = generated
    else:
        security.validate_password_strength(raw_password)

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
    # Record the establishment posting in the shared membership history (#3) so a
    # staff member's affectations are historised and can span establishments.
    db.add(models.SchoolMembership(
        user_id=user.id, school_id=resolved, role=role.value,
        start_date=datetime.utcnow(), is_active=True, membership_status="active",
    ))
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


# --- Establishment assignment history (#3) -----------------------------------

def _assignment_response(membership: models.SchoolMembership, school: Optional[models.School]) -> schemas.StaffAssignmentResponse:
    return schemas.StaffAssignmentResponse(
        id=membership.id, user_id=membership.user_id, school_id=membership.school_id,
        school_name=school.name if school else None, role=membership.role,
        membership_status=membership.membership_status, is_active=bool(membership.is_active),
        start_date=membership.start_date, end_date=membership.end_date,
    )


def _resolve_staff(db: Session, staff_id: int, school_id: int) -> models.StaffProfile:
    profile = db.query(models.StaffProfile).filter(models.StaffProfile.id == staff_id, models.StaffProfile.school_id == school_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Membre du personnel introuvable.")
    return profile


@router.get("/{staff_id}/assignments", response_model=List[schemas.StaffAssignmentResponse])
def list_staff_assignments(staff_id: int, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Full establishment-posting history of a staff member (may span several
    establishments), most recent first."""
    _ensure_admin(current_user)
    resolved = _resolve_school(current_user, school_id)
    profile = _resolve_staff(db, staff_id, resolved)
    rows = (
        db.query(models.SchoolMembership, models.School)
        .outerjoin(models.School, models.School.id == models.SchoolMembership.school_id)
        .filter(models.SchoolMembership.user_id == profile.user_id)
        .order_by(models.SchoolMembership.start_date.desc().nullslast(), models.SchoolMembership.id.desc())
        .all()
    )
    return [_assignment_response(membership, school) for membership, school in rows]


@router.post("/{staff_id}/assignments", response_model=schemas.StaffAssignmentResponse, status_code=201)
def add_staff_assignment(staff_id: int, payload: schemas.StaffAssignmentCreate, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Post a staff member to another establishment (historised). A school admin
    may only post to their own establishment; the Super Admin may post to any."""
    _ensure_admin(current_user)
    resolved = _resolve_school(current_user, school_id)
    profile = _resolve_staff(db, staff_id, resolved)
    if current_user.role != models.UserRole.SUPER_ADMIN and payload.school_id != resolved:
        raise HTTPException(status_code=403, detail="Vous ne pouvez affecter que dans votre établissement.")
    target = db.query(models.School).filter(models.School.id == payload.school_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Établissement cible introuvable.")
    if db.query(models.SchoolMembership.id).filter(
        models.SchoolMembership.user_id == profile.user_id,
        models.SchoolMembership.school_id == payload.school_id,
        models.SchoolMembership.is_active == True,  # noqa: E712
    ).first():
        raise HTTPException(status_code=409, detail="Ce membre est déjà affecté à cet établissement.")
    user = db.query(models.User).filter(models.User.id == profile.user_id).first()
    membership = models.SchoolMembership(
        user_id=profile.user_id, school_id=payload.school_id,
        role=payload.role or (user.role.value if user and user.role else "staff"),
        start_date=datetime.utcnow(), is_active=True, membership_status="active",
    )
    db.add(membership)
    audit.record_audit(db, action="personnel.assignment.added", current_user=current_user, entity_type="school_membership", entity_id=profile.user_id, details={"school_id": payload.school_id})
    db.commit()
    db.refresh(membership)
    return _assignment_response(membership, target)


@router.post("/assignments/{membership_id}/end", response_model=schemas.StaffAssignmentResponse)
def end_staff_assignment(membership_id: int, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Close a posting — sets the end date and deactivates it (kept for history)."""
    _ensure_admin(current_user)
    resolved = _resolve_school(current_user, school_id)
    membership = db.query(models.SchoolMembership).filter(models.SchoolMembership.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Affectation introuvable.")
    if current_user.role != models.UserRole.SUPER_ADMIN and membership.school_id != resolved:
        raise HTTPException(status_code=403, detail="Accès refusé.")
    membership.is_active = False
    membership.membership_status = "ended"
    membership.end_date = datetime.utcnow()
    audit.record_audit(db, action="personnel.assignment.ended", current_user=current_user, entity_type="school_membership", entity_id=membership_id)
    db.commit()
    db.refresh(membership)
    school = db.query(models.School).filter(models.School.id == membership.school_id).first()
    return _assignment_response(membership, school)
