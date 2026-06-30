"""School levels referential (#3) — a global, platform-managed list of levels
(CP1, 6ème, Terminale, BTS …) administered exclusively by the Super Admin.

Reads are open to any authenticated user (schools need the list to create
classes); writes are Super-Admin only. A level can be deleted only when no class
references it (by `Class.level == level.code`).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security

router = APIRouter(prefix="/levels", tags=["School Levels"])


def _ensure_super_admin(current_user: models.User) -> None:
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Administrateur uniquement.")


@router.get("", response_model=List[schemas.SchoolLevelResponse])
@router.get("/", response_model=List[schemas.SchoolLevelResponse], include_in_schema=False)
def list_levels(active_only: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    query = db.query(models.SchoolLevel)
    if active_only:
        query = query.filter(models.SchoolLevel.is_active == True)  # noqa: E712
    return query.order_by(models.SchoolLevel.sort_order.asc(), models.SchoolLevel.code.asc()).all()


@router.post("", response_model=schemas.SchoolLevelResponse)
@router.post("/", response_model=schemas.SchoolLevelResponse, include_in_schema=False)
def create_level(payload: schemas.SchoolLevelCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_super_admin(current_user)
    if db.query(models.SchoolLevel.id).filter(models.SchoolLevel.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Ce code de niveau existe déjà.")
    row = models.SchoolLevel(**payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="school_level.created", current_user=current_user, entity_type="school_level", details={"code": payload.code})
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{level_id}", response_model=schemas.SchoolLevelResponse)
def update_level(level_id: int, payload: schemas.SchoolLevelUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_super_admin(current_user)
    row = db.query(models.SchoolLevel).filter(models.SchoolLevel.id == level_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Niveau introuvable.")
    data = payload.model_dump(exclude_unset=True)
    if "code" in data and data["code"] != row.code and db.query(models.SchoolLevel.id).filter(models.SchoolLevel.code == data["code"]).first():
        raise HTTPException(status_code=409, detail="Ce code de niveau existe déjà.")
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{level_id}")
def delete_level(level_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_super_admin(current_user)
    row = db.query(models.SchoolLevel).filter(models.SchoolLevel.id == level_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Niveau introuvable.")
    used = db.query(models.Class.id).filter(models.Class.level == row.code).first()
    if used:
        raise HTTPException(status_code=409, detail="Ce niveau est utilisé par des classes et ne peut pas être supprimé.")
    db.delete(row)
    audit.record_audit(db, action="school_level.deleted", current_user=current_user, entity_type="school_level", details={"code": row.code})
    db.commit()
    return {"status": "deleted"}
