from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, security, database

router = APIRouter(prefix="/education", tags=["Education"])

# ---------------------------------------------------------
# Classes endpoints
# ---------------------------------------------------------

@router.post("/classes", response_model=schemas.ClassResponse)
def create_class(
    class_in: schemas.ClassCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_class = models.Class(
        name=class_in.name,
        level=class_in.level,
        school_id=current_user.school_id,
        main_teacher_id=class_in.main_teacher_id
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    return new_class

@router.get("/classes", response_model=List[schemas.ClassResponse])
def list_classes(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="User not part of a school")
        
    classes = db.query(models.Class).filter(
        models.Class.school_id == current_user.school_id
    ).offset(skip).limit(limit).all()
    return classes

@router.put("/classes/{class_id}", response_model=schemas.ClassResponse)
def update_class(
    class_id: int,
    class_in: schemas.ClassCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    cls = db.query(models.Class).filter(
        models.Class.id == class_id,
        models.Class.school_id == current_user.school_id
    ).first()
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
        
    cls.name = class_in.name
    cls.level = class_in.level
    cls.main_teacher_id = class_in.main_teacher_id
    
    db.commit()
    db.refresh(cls)
    return cls

@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    cls = db.query(models.Class).filter(
        models.Class.id == class_id,
        models.Class.school_id == current_user.school_id
    ).first()
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
        
    db.delete(cls)
    db.delete(cls)
    db.commit()

# ---------------------------------------------------------
# Years & Terms Endpoints
# ---------------------------------------------------------

@router.post("/academic-years", response_model=schemas.AcademicYearResponse)
def create_academic_year(
    year_in: schemas.AcademicYearCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    new_year = models.AcademicYear(
        **year_in.dict(),
        school_id=current_user.school_id
    )
    db.add(new_year)
    db.commit()
    db.refresh(new_year)
    return new_year

@router.post("/terms", response_model=schemas.TermResponse)
def create_term(
    term_in: schemas.TermCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    new_term = models.Term(**term_in.dict())
    db.add(new_term)
    db.commit()
    db.refresh(new_term)
    return new_term

# ---------------------------------------------------------

@router.post("/subjects", response_model=schemas.SubjectResponse)
def create_subject(
    subject_in: schemas.SubjectCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    new_sub = models.Subject(
        **subject_in.dict(),
        school_id=current_user.school_id
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.get("/subjects", response_model=List[schemas.SubjectResponse])
def list_subjects(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not current_user.school_id:
         raise HTTPException(status_code=400, detail="User not part of a school")
         
    subjects = db.query(models.Subject).filter(
        models.Subject.school_id == current_user.school_id
    ).offset(skip).limit(limit).all()
    return subjects

@router.put("/subjects/{subject_id}", response_model=schemas.SubjectResponse)
def update_subject(
    subject_id: int,
    subject_in: schemas.SubjectUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    sub = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.school_id == current_user.school_id
    ).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    update_data = subject_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sub, key, value)
        
    db.commit()
    db.refresh(sub)
    return sub

@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    sub = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.school_id == current_user.school_id
    ).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    db.delete(sub)
    db.commit()


# ---------------------------------------------------------
# Timetables endpoints
# ---------------------------------------------------------

@router.post("/timetables", response_model=schemas.TimetableResponse)
def create_timetable_entry(
    entry_in: schemas.TimetableCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Verify Class belongs to school
    cls = db.query(models.Class).filter(models.Class.id == entry_in.class_id, models.Class.school_id == current_user.school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found in this school")

    entry = models.Timetable(**entry_in.dict())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.get("/timetables", response_model=List[schemas.TimetableResponse])
def list_timetables(
    class_id: int = None,
    teacher_id: int = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="User not part of a school")
        
    query = db.query(models.Timetable).join(models.Class).filter(models.Class.school_id == current_user.school_id)
    
    if class_id:
        query = query.filter(models.Timetable.class_id == class_id)
    if teacher_id:
        query = query.filter(models.Timetable.teacher_id == teacher_id)
        
    return query.all()

@router.delete("/timetables/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable_entry(
    entry_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Join with Class to verify School context
    entry = db.query(models.Timetable).join(models.Class).filter(
        models.Timetable.id == entry_id,
        models.Class.school_id == current_user.school_id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
        
    db.delete(entry)
    db.commit()
