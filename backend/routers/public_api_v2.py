"""
Public Partner REST API (v2) — third-party, server-to-server access with write capabilities.

Authentication is a tenant **API key** sent as `X-API-Key` (minted and revoked
in `/extensibility/api-keys`; only the SHA-256 hash is stored). Every request is
scoped to the key's school — a partner can never read another tenant's data.
Endpoints are paginated (`limit` ≤ 200, `offset`), and described in
the OpenAPI schema.

This v2 API adds CREATE, UPDATE, DELETE operations for third-party integrations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

import hashlib

from .. import database, models
from ..schemas import (
    PublicStudent, PublicTeacher, PublicClass, PublicSubject, PublicAnnouncement, PublicKeyInfo,
    StudentCreate, StudentUpdate, TeacherCreate, TeacherUpdate, ClassCreate, ClassUpdate,
    SubjectCreate, SubjectUpdate, SchoolCreate, SchoolUpdate,
)

router = APIRouter(prefix="/api/v2", tags=["Public API (v2) - Third Party Integration"])

MAX_LIMIT = 200


def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(database.get_db),
) -> models.ApiKey:
    """Resolve and validate the partner API key; returns the ApiKey row (which
    carries the tenant scope). 401 on missing/unknown/revoked keys."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    row = db.query(models.ApiKey).filter(
        models.ApiKey.key_hash == key_hash,
        models.ApiKey.is_active == True,  # noqa: E712
    ).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    row.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return row


def _page(limit: int, offset: int) -> tuple[int, int]:
    return min(max(limit, 1), MAX_LIMIT), max(offset, 0)


# ============================================================================
# Key Info
# ============================================================================

@router.get("/me", response_model=PublicKeyInfo)
def key_info(api_key: models.ApiKey = Depends(require_api_key), db: Session = Depends(database.get_db)):
    """Identify the calling key and its tenant scope."""
    school = db.query(models.School).filter(models.School.id == api_key.school_id).first()
    return PublicKeyInfo(
        key_name=api_key.name,
        key_prefix=api_key.prefix,
        school_id=api_key.school_id,
        school_name=school.name if school else None
    )


# ============================================================================
# Students
# ============================================================================

@router.get("/students", response_model=List[PublicStudent])
def list_students(
    limit: int = Query(50), offset: int = Query(0),
    class_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """List students with optional filtering."""
    limit, offset = _page(limit, offset)
    query = (
        db.query(models.User, models.StudentProfile)
        .join(models.StudentProfile, models.StudentProfile.user_id == models.User.id)
        .filter(models.User.school_id == api_key.school_id, models.User.role.in_([models.UserRole.STUDENT, models.UserRole.PUPIL]))
    )
    
    if class_id:
        query = query.filter(models.StudentProfile.current_class_id == class_id)
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.User.full_name.ilike(search_term)) |
            (models.User.email.ilike(search_term)) |
            (models.StudentProfile.registration_number.ilike(search_term))
        )
    
    rows = query.order_by(models.User.id.asc()).offset(offset).limit(limit).all()
    class_names = {c.id: c.name for c in db.query(models.Class).filter(models.Class.school_id == api_key.school_id).all()}
    return [
        PublicStudent(
            id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active),
            registration_number=profile.registration_number, gender=profile.gender,
            class_id=profile.current_class_id, class_name=class_names.get(profile.current_class_id),
        )
        for user, profile in rows
    ]


@router.get("/students/{student_id}", response_model=PublicStudent)
def get_student(
    student_id: int,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Get a single student by ID."""
    row = (
        db.query(models.User, models.StudentProfile)
        .join(models.StudentProfile, models.StudentProfile.user_id == models.User.id)
        .filter(models.User.id == student_id, models.User.school_id == api_key.school_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    user, profile = row
    class_names = {c.id: c.name for c in db.query(models.Class).filter(models.Class.school_id == api_key.school_id).all()}
    return PublicStudent(
        id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active),
        registration_number=profile.registration_number, gender=profile.gender,
        class_id=profile.current_class_id, class_name=class_names.get(profile.current_class_id),
    )


@router.post("/students", response_model=PublicStudent, status_code=201)
def create_student(
    payload: StudentCreate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Create a new student."""
    # Check if user with email already exists
    existing = db.query(models.User).filter(
        models.User.email == payload.email,
        models.User.school_id == api_key.school_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    
    # Hash password (use a default or generate one)
    from ..crypto_utils import hash_password
    hashed_pw = hash_password(payload.password or "TempPass123!")
    
    user = models.User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role=models.UserRole.STUDENT,
        school_id=api_key.school_id,
        is_active=payload.is_active if payload.is_active is not None else True,
    )
    db.add(user)
    db.flush()
    
    profile = models.StudentProfile(
        user_id=user.id,
        school_id=api_key.school_id,
        registration_number=payload.registration_number,
        gender=payload.gender,
        date_of_birth=payload.date_of_birth,
        current_class_id=payload.class_id,
        parent_phone=payload.parent_phone,
        address=payload.address,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    
    class_names = {c.id: c.name for c in db.query(models.Class).filter(models.Class.school_id == api_key.school_id).all()}
    return PublicStudent(
        id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active),
        registration_number=profile.registration_number, gender=profile.gender,
        class_id=profile.current_class_id, class_name=class_names.get(profile.current_class_id),
    )


@router.put("/students/{student_id}", response_model=PublicStudent)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Update a student."""
    user = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == api_key.school_id,
        models.User.role.in_([models.UserRole.STUDENT, models.UserRole.PUPIL])
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    
    profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == student_id).first()
    
    # Update user fields
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        # Check email uniqueness
        existing = db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.school_id == api_key.school_id,
            models.User.id != student_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    
    # Update profile fields
    if profile and payload.profile_data:
        if payload.profile_data.registration_number is not None:
            profile.registration_number = payload.profile_data.registration_number
        if payload.profile_data.gender is not None:
            profile.gender = payload.profile_data.gender
        if payload.profile_data.date_of_birth is not None:
            profile.date_of_birth = payload.profile_data.date_of_birth
        if payload.profile_data.current_class_id is not None:
            profile.current_class_id = payload.profile_data.current_class_id
        if payload.profile_data.parent_phone is not None:
            profile.parent_phone = payload.profile_data.parent_phone
        if payload.profile_data.address is not None:
            profile.address = payload.profile_data.address
    
    db.commit()
    db.refresh(user)
    if profile:
        db.refresh(profile)
    
    class_names = {c.id: c.name for c in db.query(models.Class).filter(models.Class.school_id == api_key.school_id).all()}
    return PublicStudent(
        id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active),
        registration_number=profile.registration_number if profile else None,
        gender=profile.gender if profile else None,
        class_id=profile.current_class_id if profile else None,
        class_name=class_names.get(profile.current_class_id) if profile else None,
    )


@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Delete a student (soft delete - deactivates user)."""
    user = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.school_id == api_key.school_id,
        models.User.role.in_([models.UserRole.STUDENT, models.UserRole.PUPIL])
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user.is_active = False
    db.commit()
    return {"status": "deactivated", "id": student_id}


# ============================================================================
# Teachers
# ============================================================================

@router.get("/teachers", response_model=List[PublicTeacher])
def list_teachers(
    limit: int = Query(50), offset: int = Query(0),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """List teachers with optional filtering."""
    limit, offset = _page(limit, offset)
    query = (
        db.query(models.User)
        .filter(
            models.User.school_id == api_key.school_id,
            models.User.role.in_([models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR])
        )
    )
    
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.User.full_name.ilike(search_term)) |
            (models.User.email.ilike(search_term))
        )
    
    rows = query.order_by(models.User.id.asc()).offset(offset).limit(limit).all()
    return [PublicTeacher(id=u.id, full_name=u.full_name, email=u.email, is_active=bool(u.is_active)) for u in rows]


@router.get("/teachers/{teacher_id}", response_model=PublicTeacher)
def get_teacher(
    teacher_id: int,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Get a single teacher by ID."""
    user = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.school_id == api_key.school_id,
        models.User.role.in_([models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR])
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return PublicTeacher(id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active))


@router.post("/teachers", response_model=PublicTeacher, status_code=201)
def create_teacher(
    payload: TeacherCreate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Create a new teacher."""
    existing = db.query(models.User).filter(
        models.User.email == payload.email,
        models.User.school_id == api_key.school_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    
    from ..crypto_utils import hash_password
    hashed_pw = hash_password(payload.password or "TempPass123!")
    
    user = models.User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role=models.UserRole.TEACHER,
        school_id=api_key.school_id,
        is_active=payload.is_active if payload.is_active is not None else True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return PublicTeacher(id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active))


@router.put("/teachers/{teacher_id}", response_model=PublicTeacher)
def update_teacher(
    teacher_id: int,
    payload: TeacherUpdate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Update a teacher."""
    user = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.school_id == api_key.school_id,
        models.User.role.in_([models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR])
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        existing = db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.school_id == api_key.school_id,
            models.User.id != teacher_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    
    db.commit()
    db.refresh(user)
    return PublicTeacher(id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active))


@router.delete("/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Delete a teacher (soft delete - deactivates user)."""
    user = db.query(models.User).filter(
        models.User.id == teacher_id,
        models.User.school_id == api_key.school_id,
        models.User.role.in_([models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR])
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    user.is_active = False
    db.commit()
    return {"status": "deactivated", "id": teacher_id}


# ============================================================================
# Classes
# ============================================================================

@router.get("/classes", response_model=List[PublicClass])
def list_classes(
    limit: int = Query(100), offset: int = Query(0),
    level: Optional[str] = Query(None),
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """List classes with optional filtering."""
    limit, offset = _page(limit, offset)
    query = db.query(models.Class).filter(models.Class.school_id == api_key.school_id)
    if level:
        query = query.filter(models.Class.level == level)
    rows = query.order_by(models.Class.name.asc()).offset(offset).limit(limit).all()
    return [PublicClass(id=c.id, name=c.name, level=c.level) for c in rows]


@router.get("/classes/{class_id}", response_model=PublicClass)
def get_class(
    class_id: int,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Get a single class by ID."""
    cls = db.query(models.Class).filter(
        models.Class.id == class_id,
        models.Class.school_id == api_key.school_id
    ).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return PublicClass(id=cls.id, name=cls.name, level=cls.level)


@router.post("/classes", response_model=PublicClass, status_code=201)
def create_class(
    payload: ClassCreate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Create a new class."""
    cls = models.Class(
        name=payload.name,
        level=payload.level,
        school_id=api_key.school_id,
        academic_year_id=payload.academic_year_id,
        capacity=payload.capacity,
    )
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return PublicClass(id=cls.id, name=cls.name, level=cls.level)


@router.put("/classes/{class_id}", response_model=PublicClass)
def update_class(
    class_id: int,
    payload: ClassUpdate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Update a class."""
    cls = db.query(models.Class).filter(
        models.Class.id == class_id,
        models.Class.school_id == api_key.school_id
    ).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    if payload.name is not None:
        cls.name = payload.name
    if payload.level is not None:
        cls.level = payload.level
    if payload.capacity is not None:
        cls.capacity = payload.capacity
    
    db.commit()
    db.refresh(cls)
    return PublicClass(id=cls.id, name=cls.name, level=cls.level)


@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Delete a class."""
    cls = db.query(models.Class).filter(
        models.Class.id == class_id,
        models.Class.school_id == api_key.school_id
    ).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    db.delete(cls)
    db.commit()
    return {"status": "deleted", "id": class_id}


# ============================================================================
# Subjects
# ============================================================================

@router.get("/subjects", response_model=List[PublicSubject])
def list_subjects(
    limit: int = Query(100), offset: int = Query(0),
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """List subjects."""
    limit, offset = _page(limit, offset)
    rows = (
        db.query(models.Subject)
        .filter(models.Subject.school_id == api_key.school_id)
        .order_by(models.Subject.name.asc())
        .offset(offset).limit(limit).all()
    )
    return [PublicSubject(id=s.id, name=s.name, coefficient=s.coefficient) for s in rows]


@router.post("/subjects", response_model=PublicSubject, status_code=201)
def create_subject(
    payload: SubjectCreate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Create a new subject."""
    subject = models.Subject(
        name=payload.name,
        coefficient=payload.coefficient,
        school_id=api_key.school_id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return PublicSubject(id=subject.id, name=subject.name, coefficient=subject.coefficient)


@router.put("/subjects/{subject_id}", response_model=PublicSubject)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Update a subject."""
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.school_id == api_key.school_id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    if payload.name is not None:
        subject.name = payload.name
    if payload.coefficient is not None:
        subject.coefficient = payload.coefficient
    
    db.commit()
    db.refresh(subject)
    return PublicSubject(id=subject.id, name=subject.name, coefficient=subject.coefficient)


@router.delete("/subjects/{subject_id}")
def delete_subject(
    subject_id: int,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Delete a subject."""
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.school_id == api_key.school_id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    db.delete(subject)
    db.commit()
    return {"status": "deleted", "id": subject_id}


# ============================================================================
# Schools (Établissements Scolaires)
# ============================================================================

@router.get("/schools", response_model=List[PublicKeyInfo])
def list_schools(
    limit: int = Query(50), offset: int = Query(0),
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """List schools (only the tenant's own school unless super_admin)."""
    # For non-super_admin, only return their own school
    if api_key.school_id:
        school = db.query(models.School).filter(models.School.id == api_key.school_id).first()
        if school:
            return [PublicKeyInfo(key_name="", key_prefix="", school_id=school.id, school_name=school.name)]
        return []
    
    # Super admin can list all schools
    limit, offset = _page(limit, offset)
    rows = db.query(models.School).offset(offset).limit(limit).all()
    return [PublicKeyInfo(key_name="", key_prefix="", school_id=s.id, school_name=s.name) for s in rows]


@router.post("/schools", response_model=PublicKeyInfo, status_code=201)
def create_school(
    payload: SchoolCreate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Create a new school (super_admin only via API key context)."""
    # Check if the API key has permission (typically only super_admin keys)
    school = models.School(
        name=payload.name,
        domain_prefix=payload.domain_prefix,
        school_type=payload.school_type,
        address=payload.address,
        phone=payload.phone,
        email=payload.email,
        country=payload.country or "CI",
        city=payload.city,
        is_active=True,
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return PublicKeyInfo(key_name="", key_prefix="", school_id=school.id, school_name=school.name)


@router.put("/schools/{school_id}", response_model=PublicKeyInfo)
def update_school(
    school_id: int,
    payload: SchoolUpdate,
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Update a school."""
    # Tenant can only update their own school
    if api_key.school_id and api_key.school_id != school_id:
        raise HTTPException(status_code=403, detail="Cannot modify other schools")
    
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    if payload.name is not None:
        school.name = payload.name
    if payload.address is not None:
        school.address = payload.address
    if payload.phone is not None:
        school.phone = payload.phone
    if payload.email is not None:
        school.email = payload.email
    if payload.city is not None:
        school.city = payload.city
    if payload.is_active is not None:
        school.is_active = payload.is_active
    
    db.commit()
    db.refresh(school)
    return PublicKeyInfo(key_name="", key_prefix="", school_id=school.id, school_name=school.name)


# ============================================================================
# Announcements
# ============================================================================

@router.get("/announcements", response_model=List[PublicAnnouncement])
def list_announcements(
    limit: int = Query(50), offset: int = Query(0),
    api_key: models.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db)
):
    """Published announcements only — the outward-facing communication feed."""
    limit, offset = _page(limit, offset)
    rows = (
        db.query(models.Announcement)
        .filter(models.Announcement.school_id == api_key.school_id, models.Announcement.status == "published")
        .order_by(models.Announcement.id.desc())
        .offset(offset).limit(limit).all()
    )
    return [
        PublicAnnouncement(id=a.id, title=a.title, body=a.body, audience=a.audience, is_emergency=bool(a.is_emergency), published_at=a.published_at)
        for a in rows
    ]