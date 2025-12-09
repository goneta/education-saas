from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, security, database

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/", response_model=schemas.StudentResponse)
def register_student(
    student_in: schemas.StudentCreateSchema, 
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. Permission Check (Only Admin can register students for now)
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to register students")
    
    # 2. Check if user email exists
    if db.query(models.User).filter(models.User.email == student_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # 3. Check if registration number exists (in this school)
    # Ideally should scope by school, but for MVP global unique is safer or scope query
    existing_profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.registration_number == student_in.profile.registration_number
    ).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Registration number (matricule) already exists")

    try:
        # 4. Create User
        hashed_password = security.get_password_hash(student_in.password)
        new_user = models.User(
            email=student_in.email,
            hashed_password=hashed_password,
            full_name=student_in.full_name,
            role=models.UserRole.STUDENT,
            school_id=current_user.school_id, # Link to Admin's school
            is_active=True
        )
        db.add(new_user)
        db.flush() # Flush to get new_user.id for profile

        # 5. Create Profile
        new_profile = models.StudentProfile(
            user_id=new_user.id,
            registration_number=student_in.profile.registration_number,
            date_of_birth=student_in.profile.date_of_birth,
            gender=student_in.profile.gender,
            student_address=student_in.profile.student_address,
            parent_name=student_in.profile.parent_name,
            parent_phone=student_in.profile.parent_phone,
            parent_email=student_in.profile.parent_email,
            parent_address=student_in.profile.parent_address,
            current_class_id=student_in.profile.current_class_id
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.StudentResponse])
def list_students(
    skip: int = 0, 
    limit: int = 100, 
    class_id: int = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Ensure user belongs to a school
    if not current_user.school_id:
         raise HTTPException(status_code=400, detail="User not associated with a school")

    query = db.query(models.User).join(models.StudentProfile).\
        filter(models.User.school_id == current_user.school_id).\
        filter(models.User.role == models.UserRole.STUDENT)
    
    if class_id:
        query = query.filter(models.StudentProfile.current_class_id == class_id)
        
    students = query.offset(skip).limit(limit).all()
    return students
