from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from .. import localization, models, schemas, security, database
from ..services import automation

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
        security.validate_password_strength(student_in.password)
        school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
        country_code = school.country_code if school else "CI"
        valid_phone, parent_phone_e164, phone_error = localization.validate_phone(
            student_in.profile.parent_phone,
            student_in.profile.parent_phone_country_code or country_code,
        )
        if not valid_phone:
            raise HTTPException(status_code=400, detail=phone_error)
        student_address_structured = student_in.profile.student_address_structured.model_dump() if student_in.profile.student_address_structured else None
        parent_address_structured = student_in.profile.parent_address_structured.model_dump() if student_in.profile.parent_address_structured else None
        if student_address_structured and not student_address_structured.get("country"):
            student_address_structured["country"] = localization.country_profile(country_code)["name"]
        if parent_address_structured and not parent_address_structured.get("country"):
            parent_address_structured["country"] = localization.country_profile(country_code)["name"]
        student_formatted_address = localization.format_address(student_address_structured) or student_in.profile.student_address
        parent_formatted_address = localization.format_address(parent_address_structured) or student_in.profile.parent_address

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
            student_address_structured=student_address_structured,
            student_formatted_address=student_formatted_address,
            parent_name=student_in.profile.parent_name,
            parent_phone=student_in.profile.parent_phone,
            parent_phone_country_code=student_in.profile.parent_phone_country_code or country_code,
            parent_phone_e164=parent_phone_e164,
            parent_email=student_in.profile.parent_email,
            parent_address=student_in.profile.parent_address,
            parent_address_structured=parent_address_structured,
            parent_formatted_address=parent_formatted_address,
            guardian_relation=student_in.profile.guardian_relation,
            status=student_in.profile.status,
            previous_level=student_in.profile.previous_level,
            previous_class=student_in.profile.previous_class,
            current_class_id=student_in.profile.current_class_id
        )
        db.add(new_profile)
        db.flush()
        for document_name in [
            "Extrait de naissance",
            "Bulletin scolaire de l'annee derniere",
            "Piece d'identite parent 1",
            "Piece d'identite parent 2 ou representant legal",
        ]:
            db.add(models.StudentRegistrationDocument(student_id=new_profile.id, name=document_name))
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[schemas.StudentResponse])
def list_students(
    skip: int = 0, 
    limit: int = 100, 
    class_id: int = None,
    search: str = None,
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
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (models.User.full_name.ilike(pattern)) |
            (models.StudentProfile.registration_number.ilike(pattern))
        )
        
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


def _student_outstanding_balance(student_profile: models.StudentProfile) -> float:
    return sum(
        max(fee.amount - sum(payment.amount for payment in fee.payments), 0)
        for fee in getattr(student_profile, "fees", [])
    )

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
            school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
            country_code = school.country_code if school else "CI"
            profile_data = student_in.profile.model_dump(exclude_unset=True)
            if "parent_phone" in profile_data or "parent_phone_country_code" in profile_data:
                raw_phone = profile_data.get("parent_phone", student.student_profile.parent_phone)
                phone_country = profile_data.get("parent_phone_country_code") or student.student_profile.parent_phone_country_code or country_code
                valid_phone, parent_phone_e164, phone_error = localization.validate_phone(raw_phone, phone_country)
                if not valid_phone:
                    raise HTTPException(status_code=400, detail=phone_error)
                profile_data["parent_phone_e164"] = parent_phone_e164
                profile_data["parent_phone_country_code"] = phone_country
            if "student_address_structured" in profile_data:
                structured = profile_data["student_address_structured"]
                if structured and not structured.get("country"):
                    structured["country"] = localization.country_profile(country_code)["name"]
                profile_data["student_formatted_address"] = localization.format_address(structured)
            if "parent_address_structured" in profile_data:
                structured = profile_data["parent_address_structured"]
                if structured and not structured.get("country"):
                    structured["country"] = localization.country_profile(country_code)["name"]
                profile_data["parent_formatted_address"] = localization.format_address(structured)
            for key, value in profile_data.items():
                setattr(student.student_profile, key, value)

    try:
        db.commit()
        db.refresh(student)
        return student
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")

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


@router.post("/{student_id}/certificates", response_model=schemas.CertificateResponse)
def generate_certificate(
    student_id: int,
    certificate_in: schemas.CertificateCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    student = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == current_user.school_id,
        models.User.role == models.UserRole.STUDENT
    ).first()
    if not student or not student.student_profile:
        raise HTTPException(status_code=404, detail="Student not found")

    fees = db.query(models.Fee).filter(models.Fee.student_id == student.student_profile.id).all()
    outstanding = sum(max(fee.amount - sum(payment.amount for payment in fee.payments), 0) for fee in fees)
    blocked = certificate_in.certificate_type != models.CertificateType.SCHOOLING and outstanding > 0
    school = student.school
    content = None if blocked else (
        f"{certificate_in.certificate_type.value} - {student.full_name} "
        f"({student.student_profile.registration_number}) - {school.name if school else ''}"
    )
    row = models.CertificateRequest(
        certificate_type=certificate_in.certificate_type,
        status=models.CertificateStatus.BLOCKED if blocked else models.CertificateStatus.GENERATED,
        blocked_reason="Attestation bloquée: solde financier impayé." if blocked else None,
        content=content,
        student_id=student.student_profile.id,
        school_id=current_user.school_id,
        generated_by_id=current_user.id,
    )
    db.add(row)
    db.flush()
    automation.automate_certificate(db, row, current_user)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{student_id}/certificates", response_model=List[schemas.CertificateResponse])
def list_certificates(
    student_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    student = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == current_user.school_id,
        models.User.role == models.UserRole.STUDENT
    ).first()
    if not student or not student.student_profile:
        raise HTTPException(status_code=404, detail="Student not found")
    return db.query(models.CertificateRequest).filter(
        models.CertificateRequest.student_id == student.student_profile.id,
        models.CertificateRequest.school_id == current_user.school_id,
    ).order_by(models.CertificateRequest.generated_at.desc()).all()


@router.get("/{student_id}/documents", response_model=List[schemas.RegistrationDocumentResponse])
def list_registration_documents(
    student_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    student = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == current_user.school_id,
        models.User.role == models.UserRole.STUDENT
    ).first()
    if not student or not student.student_profile:
        raise HTTPException(status_code=404, detail="Student not found")
    return student.student_profile.registration_documents


@router.put("/{student_id}/documents/{document_id}", response_model=schemas.RegistrationDocumentResponse)
def update_registration_document(
    student_id: int,
    document_id: int,
    document_in: schemas.RegistrationDocumentUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [
        models.UserRole.SCHOOL_ADMIN,
        models.UserRole.SUPER_ADMIN,
        models.UserRole.REGISTRAR,
        models.UserRole.DIRECTION,
    ]:
        raise HTTPException(status_code=403, detail="Not authorized")

    document = db.query(models.StudentRegistrationDocument).join(models.StudentProfile).join(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == current_user.school_id,
        models.StudentRegistrationDocument.id == document_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.name = document_in.name
    document.is_received = document_in.is_received
    document.notes = document_in.notes
    document.updated_by_id = current_user.id
    document.received_at = datetime.utcnow() if document_in.is_received and not document.received_at else None if not document_in.is_received else document.received_at
    db.commit()
    db.refresh(document)
    return document
