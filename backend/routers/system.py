from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from .. import models, schemas, security, database

router = APIRouter(prefix="/system", tags=["System Configuration"])

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
