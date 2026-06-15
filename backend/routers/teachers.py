from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import localization, models, schemas, security, database, tenancy

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.post("/", response_model=schemas.TeacherResponse)
def register_teacher(
    teacher_in: schemas.TeacherCreate, 
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. Permission Check (Only Admin can register teachers)
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to register teachers")
    
    school_id = tenancy.resolve_school_id_for_create(current_user, teacher_in.school_id, db)
    existing_person = tenancy.find_existing_person(db, email=teacher_in.email, full_name=teacher_in.full_name)
    if existing_person:
        if teacher_in.transfer_reason:
            existing_person.school_id = school_id
            existing_person.role = models.UserRole.TEACHER
            if not existing_person.teacher_profile:
                existing_person.teacher_profile = models.TeacherProfile(
                    user_id=existing_person.id,
                    specialization=teacher_in.profile.specialization,
                    join_date=teacher_in.profile.join_date,
                    bio=teacher_in.profile.bio,
                )
                db.add(existing_person.teacher_profile)
            tenancy.create_or_transfer_school_membership(
                db,
                user=existing_person,
                school_id=school_id,
                role=models.UserRole.TEACHER.value,
                transfer_reason=teacher_in.transfer_reason,
            )
            db.commit()
            db.refresh(existing_person)
            return existing_person
        raise HTTPException(status_code=409, detail="Cette personne existe déjà dans le système. Voulez-vous l'associer ou la transférer vers cette école tout en conservant son historique ?")
        
    try:
        security.validate_password_strength(teacher_in.password)
        # 3. Create User
        hashed_password = security.get_password_hash(teacher_in.password)
        new_user = models.User(
            email=teacher_in.email,
            hashed_password=hashed_password,
            full_name=teacher_in.full_name,
            role=models.UserRole.TEACHER,
            school_id=school_id,
            is_active=True
        )
        db.add(new_user)
        db.flush() # Flush to get new_user.id for profile

        # 4. Create Profile
        new_profile = models.TeacherProfile(
            user_id=new_user.id,
            specialization=teacher_in.profile.specialization,
            join_date=teacher_in.profile.join_date,
            bio=teacher_in.profile.bio
        )
        db.add(new_profile)
        tenancy.create_or_transfer_school_membership(
            db,
            user=new_user,
            school_id=school_id,
            role=models.UserRole.TEACHER.value,
            transfer_reason=teacher_in.transfer_reason,
        )
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[schemas.TeacherResponse])
def list_teachers(
    skip: int = 0, 
    limit: int = 100, 
    school_id: int = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.User).join(models.TeacherProfile).\
        filter(models.User.role == models.UserRole.TEACHER)
    query = tenancy.apply_user_school_filter(query, current_user, school_id)
        
    teachers = query.offset(skip).limit(limit).all()
    return teachers

@router.get("/{teacher_id}", response_model=schemas.TeacherResponse)
def get_teacher(
    teacher_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    teacher = db.query(models.User).filter(
        models.User.id == teacher_id, 
        models.User.role == models.UserRole.TEACHER
    )
    teacher = tenancy.apply_user_school_filter(teacher, current_user).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
        
    return teacher

@router.put("/{teacher_id}", response_model=schemas.TeacherResponse)
def update_teacher(
    teacher_id: int,
    teacher_in: schemas.TeacherUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Permission Check
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to update teachers")

    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
    )
    teacher = tenancy.apply_user_school_filter(teacher, current_user).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Update User Fields
    if teacher_in.full_name:
        teacher.full_name = teacher_in.full_name
    if teacher_in.email:
        if teacher_in.email != teacher.email:
             if db.query(models.User).filter(models.User.email == teacher_in.email).first():
                 raise HTTPException(status_code=400, detail="Email already registered")
             teacher.email = teacher_in.email
    if teacher_in.phone_number:
        school = db.query(models.School).filter(models.School.id == teacher.school_id).first()
        country_code = school.country_code if school else "CI"
        phone_country = teacher_in.phone_country_code or teacher.phone_country_code or country_code
        valid_phone, phone_e164, phone_error = localization.validate_phone(teacher_in.phone_number, phone_country)
        if not valid_phone:
            raise HTTPException(status_code=400, detail=phone_error)
        teacher.phone_number = teacher_in.phone_number
        teacher.phone_country_code = phone_country
        teacher.phone_e164 = phone_e164
    if teacher_in.address:
        teacher.address = teacher_in.address
    if teacher_in.address_structured:
        school = db.query(models.School).filter(models.School.id == teacher.school_id).first()
        country_code = school.country_code if school else "CI"
        structured = teacher_in.address_structured.model_dump()
        if not structured.get("country"):
            structured["country"] = localization.country_profile(country_code)["name"]
        structured["formatted"] = localization.format_address(structured)
        teacher.address_structured = structured
        teacher.formatted_address = structured["formatted"]
        teacher.address = structured["formatted"]

    # Update Profile Fields
    if teacher_in.profile:
        if not teacher.teacher_profile:
             # Create if missing (sanity check)
             new_profile = models.TeacherProfile(user_id=teacher.id)
             db.add(new_profile)
             teacher.teacher_profile = new_profile
        
        profile_data = teacher_in.profile.dict(exclude_unset=True)
        for key, value in profile_data.items():
            setattr(teacher.teacher_profile, key, value)

    try:
        db.commit()
        db.refresh(teacher)
        return teacher
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Permission Check
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to delete teachers")

    teacher = db.query(models.User).filter(
        models.User.id == teacher_id,
    )
    teacher = tenancy.apply_user_school_filter(teacher, current_user).first()

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    try:
        if teacher.teacher_profile:
            db.delete(teacher.teacher_profile)
            
        db.delete(teacher)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
