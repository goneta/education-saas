"""Core Platform admin API — departments, feature flags, and global search.

Slice 1 of the Goal Forge plan: closes the three Loop 1 gaps the SPEC flagged
(Department entity, Feature flags, Global search). Everything is tenant-scoped;
writes are gated to administrators.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(prefix="/platform", tags=["Core Platform"])

ADMIN_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _ensure_admin(current_user: models.User) -> None:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


# --------------------------------------------------------------------------- #
# Departments
# --------------------------------------------------------------------------- #
@router.get("/departments", response_model=List[schemas.DepartmentResponse])
def list_departments(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.Department)
        .filter(models.Department.school_id == _school_id(current_user))
        .order_by(models.Department.name.asc())
        .all()
    )


@router.post("/departments", response_model=schemas.DepartmentResponse)
def create_department(payload: schemas.DepartmentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    row = models.Department(**payload.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/departments/{department_id}", response_model=schemas.DepartmentResponse)
def update_department(department_id: int, payload: schemas.DepartmentUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    row = db.query(models.Department).filter(models.Department.id == department_id, models.Department.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Département introuvable")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/departments/{department_id}")
def delete_department(department_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    row = db.query(models.Department).filter(models.Department.id == department_id, models.Department.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Département introuvable")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Feature flags (school override falls back to the platform default)
# --------------------------------------------------------------------------- #
def feature_enabled(db: Session, key: str, school_id: Optional[int]) -> bool:
    """True when `key` is enabled for the school, falling back to the platform
    default (school_id NULL). Reusable by any module to gate a capability."""
    if school_id is not None:
        override = db.query(models.FeatureFlag).filter(models.FeatureFlag.key == key, models.FeatureFlag.school_id == school_id).first()
        if override is not None:
            return override.is_enabled
    default = db.query(models.FeatureFlag).filter(models.FeatureFlag.key == key, models.FeatureFlag.school_id.is_(None)).first()
    return bool(default.is_enabled) if default else False


@router.get("/feature-flags", response_model=List[schemas.FeatureFlagResponse])
def list_feature_flags(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Platform defaults plus this institution's overrides."""
    school_id = _school_id(current_user)
    return db.query(models.FeatureFlag).filter(or_(models.FeatureFlag.school_id == school_id, models.FeatureFlag.school_id.is_(None))).order_by(models.FeatureFlag.key.asc()).all()


@router.put("/feature-flags", response_model=schemas.FeatureFlagResponse)
def set_feature_flag(payload: schemas.FeatureFlagSet, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Set this institution's override for a flag (upsert on key+school)."""
    _ensure_admin(current_user)
    school_id = _school_id(current_user)
    row = db.query(models.FeatureFlag).filter(models.FeatureFlag.key == payload.key, models.FeatureFlag.school_id == school_id).first()
    if not row:
        row = models.FeatureFlag(key=payload.key, school_id=school_id)
        db.add(row)
    row.is_enabled = payload.is_enabled
    if payload.description is not None:
        row.description = payload.description
    db.commit()
    db.refresh(row)
    return row


# --------------------------------------------------------------------------- #
# Global search (cross-module, tenant-scoped)
# --------------------------------------------------------------------------- #
@router.get("/search")
def global_search(q: str, limit: int = 10, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Search core entities the user's institution owns. Returns typed, capped
    result groups. Tenant isolation is enforced on every query."""
    school_id = _school_id(current_user)
    term = (q or "").strip()
    if len(term) < 2:
        return {"query": term, "results": []}
    like = f"%{term}%"
    results = []

    students = (
        db.query(models.User)
        .join(models.StudentProfile, models.StudentProfile.user_id == models.User.id)
        .filter(models.User.school_id == school_id, models.User.role == models.UserRole.STUDENT)
        .filter(or_(models.User.full_name.ilike(like), models.User.email.ilike(like), models.StudentProfile.registration_number.ilike(like)))
        .limit(limit)
        .all()
    )
    results.extend({"type": "student", "id": user.id, "label": user.full_name, "sublabel": user.email} for user in students)

    teachers = (
        db.query(models.User)
        .filter(models.User.school_id == school_id, models.User.role == models.UserRole.TEACHER)
        .filter(or_(models.User.full_name.ilike(like), models.User.email.ilike(like)))
        .limit(limit)
        .all()
    )
    results.extend({"type": "teacher", "id": user.id, "label": user.full_name, "sublabel": user.email} for user in teachers)

    classes = (
        db.query(models.Class)
        .filter(models.Class.school_id == school_id, models.Class.name.ilike(like))
        .limit(limit)
        .all()
    )
    results.extend({"type": "class", "id": cls.id, "label": cls.name, "sublabel": getattr(cls, "level", None)} for cls in classes)

    fees = (
        db.query(models.Fee)
        .filter(models.Fee.school_id == school_id, models.Fee.title.ilike(like))
        .limit(limit)
        .all()
    )
    results.extend({"type": "fee", "id": fee.id, "label": fee.title, "sublabel": f"{fee.amount}"} for fee in fees)

    return {"query": term, "count": len(results), "results": results}
