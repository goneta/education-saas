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

@router.get("/{student_id}", response_model=schemas.StudentResponse)
def get_student(
    student_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    student = db.query(models.User).filter(
        models.User.id == student_id, 
        models.User.school_id == current_user.school_id, # Scoped to school
        models.User.role == models.UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    return student

@router.put("/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    student_id: int,
    student_in: schemas.StudentUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Permission Check
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to update students")

    student = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == current_user.school_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Update User Fields
    if student_in.full_name:
        student.full_name = student_in.full_name
    if student_in.email:
        # Check uniqueness if email changed
        if student_in.email != student.email:
             if db.query(models.User).filter(models.User.email == student_in.email).first():
                 raise HTTPException(status_code=400, detail="Email already registered")
             student.email = student_in.email

    # Update Profile Fields
    if student_in.profile:
        # Ensure profile exists (it should for students)
        if not student.student_profile:
             # Should not happen ideally if data integrity is kept
             pass 
        else:
            profile_data = student_in.profile.dict(exclude_unset=True)
            for key, value in profile_data.items():
                setattr(student.student_profile, key, value)

    try:
        db.commit()
        db.refresh(student)
        return student
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Permission Check
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to delete students")

    student = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == current_user.school_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        # Cascade delete handled by DB FK usually, or manual:
        # Check if we need to manually delete profile? 
        # SQLAlchemy relationship with cascade='all, delete' on User.student_profile would handle this.
        # Assuming database level Key constraints or Model cascade is set.
        # For safety, we delete user, profile should follow if configured, or we delete profile first.
        
        if student.student_profile:
            db.delete(student.student_profile)
            
        db.delete(student)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{student_id}/history", response_model=schemas.EducationHistoryResponse)
def add_education_history(
    student_id: int,
    history_in: schemas.EducationHistoryCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.STUDENT]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # If student, can only add to own profile
    if current_user.role == models.UserRole.STUDENT and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Cannot edit other students")

    student = db.query(models.User).filter(models.User.id == student_id).first()
    if not student or not student.student_profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    new_history = models.StudentEducationHistory(
        student_id=student.student_profile.id,
        **history_in.model_dump()
    )
    db.add(new_history)
    try:
        db.commit()
        db.refresh(new_history)
        return new_history
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education_history(
    history_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    history = db.query(models.StudentEducationHistory).filter(models.StudentEducationHistory.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="History record not found")
        
    # Permission check: Admin or the student themselves
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == history.student_id).first()
    if current_user.role == models.UserRole.STUDENT:
        if not student or student.user_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
         raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(history)
    db.commit()
