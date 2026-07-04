from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, selectinload
from typing import List
from datetime import datetime

from .. import localization, models, rbac, schemas, security, database, tenancy
from ..services import school_context, teacher_assignments

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.post("", response_model=schemas.TeacherResponse)
@router.post("/", response_model=schemas.TeacherResponse, include_in_schema=False)
def register_teacher(
    teacher_in: schemas.TeacherCreate, 
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. Permission Check (Only Admin can register teachers)
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to register teachers")
    
    school_id = tenancy.resolve_school_id_for_create(current_user, teacher_in.school_id, db)
    active_context = school_context.resolve_context(db, current_user)
    if active_context.school_id != school_id:
        raise HTTPException(status_code=403, detail="Le contexte actif ne correspond pas a cet etablissement.")
    existing_person = tenancy.find_existing_person(db, email=teacher_in.email, full_name=teacher_in.full_name)
    if existing_person:
        if teacher_in.transfer_reason:
            existing_person.school_id = school_id
            existing_person.role = models.UserRole.TEACHER
            if not existing_person.teacher_profile:
                existing_person.teacher_profile = models.TeacherProfile(
                    user_id=existing_person.id,
                    school_model_assignment_id=active_context.school_model_assignment_id,
                    specialization=teacher_in.profile.specialization,
                    join_date=teacher_in.profile.join_date,
                    bio=teacher_in.profile.bio,
                )
                db.add(existing_person.teacher_profile)
            existing_person.teacher_profile.school_model_assignment_id = active_context.school_model_assignment_id
            tenancy.create_or_transfer_school_membership(
                db,
                user=existing_person,
                school_id=school_id,
                role=models.UserRole.TEACHER.value,
                transfer_reason=teacher_in.transfer_reason,
            )
            teacher_assignments.ensure_assignment(
                db,
                user_id=existing_person.id,
                school_id=school_id,
                school_model_assignment_id=active_context.school_model_assignment_id,
                specialization=teacher_in.profile.specialization,
                created_by_user_id=current_user.id,
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
            school_model_assignment_id=active_context.school_model_assignment_id,
            specialization=teacher_in.profile.specialization,
            join_date=teacher_in.profile.join_date,
            bio=teacher_in.profile.bio
        )
        db.add(new_profile)
        db.flush()
        tenancy.create_or_transfer_school_membership(
            db,
            user=new_user,
            school_id=school_id,
            role=models.UserRole.TEACHER.value,
            transfer_reason=teacher_in.transfer_reason,
        )
        teacher_assignments.ensure_assignment(
            db,
            user_id=new_user.id,
            school_id=school_id,
            school_model_assignment_id=active_context.school_model_assignment_id,
            specialization=teacher_in.profile.specialization,
            created_by_user_id=current_user.id,
        )
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("", response_model=List[schemas.TeacherResponse])
@router.get("/", response_model=List[schemas.TeacherResponse], include_in_schema=False)
def list_teachers(
    skip: int = 0, 
    limit: int = 100, 
    school_id: int = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    rbac.require_permission(current_user, "teachers:view", db)
    # Teachers are listed by active teaching assignment, so a teacher engaged at
    # several schools appears in each school's list (not only their primary one).
    # Tolerant on read: teachers with no assignment row (legacy data) or whose
    # assignment predates the model-assignment concept (NULL) fall back to their
    # home school + teaching role instead of silently disappearing.
    active_context = school_context.resolve_context(db, current_user)
    assignment_match = and_(
        models.TeacherAssignment.user_id == models.User.id,
        models.TeacherAssignment.is_active == True,  # noqa: E712
        or_(
            models.TeacherAssignment.school_model_assignment_id == active_context.school_model_assignment_id,
            and_(
                models.TeacherAssignment.school_model_assignment_id == None,
                models.TeacherAssignment.school_id == active_context.school_id,
            ),
        ),
    )
    teaching_roles = [models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR]
    query = db.query(models.User).options(selectinload(models.User.teacher_profile)).outerjoin(
        models.TeacherAssignment, assignment_match
    ).filter(
        models.User.deleted_at == None,
        or_(
            models.TeacherAssignment.id != None,
            and_(
                models.User.school_id == active_context.school_id,
                models.User.role.in_(teaching_roles),
            ),
        ),
    )
    if school_id and current_user.role == models.UserRole.SUPER_ADMIN:
        query = query.filter(or_(models.TeacherAssignment.school_id == school_id, models.User.school_id == school_id))
    teachers = query.distinct().order_by(models.User.full_name.asc(), models.User.id.asc()).offset(skip).limit(limit).all()
    return teachers


@router.get("/diagnostics")
def list_teachers_diagnostics(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Explain an empty teacher list: resolved context + stage-by-stage counts
    of the EXACT filters `GET /teachers` applies, and where teaching-role users
    actually live. Admin tool for production triage — read-only."""
    rbac.require_permission(current_user, "teachers:view", db)
    if current_user.role not in (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION):
        raise HTTPException(status_code=403, detail="Réservé à l'administration.")
    ctx = school_context.resolve_context(db, current_user)
    teaching_roles = [models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR]

    teaching_users_total = db.query(models.User).filter(
        models.User.deleted_at == None,  # noqa: E711
        models.User.role.in_(teaching_roles),
    ).count()
    school_match = db.query(models.User).filter(
        models.User.deleted_at == None,  # noqa: E711
        models.User.role.in_(teaching_roles),
        models.User.school_id == ctx.school_id,
    ).count()
    assignment_match = db.query(models.TeacherAssignment).filter(
        models.TeacherAssignment.is_active == True,  # noqa: E712
        or_(
            models.TeacherAssignment.school_model_assignment_id == ctx.school_model_assignment_id,
            and_(
                models.TeacherAssignment.school_model_assignment_id == None,  # noqa: E711
                models.TeacherAssignment.school_id == ctx.school_id,
            ),
        ),
    ).count()
    final_count = len(list_teachers(skip=0, limit=100000, school_id=None, current_user=current_user, db=db))

    teacher_school_ids = [row[0] for row in (
        db.query(models.User.school_id)
        .filter(models.User.deleted_at == None, models.User.role.in_(teaching_roles))  # noqa: E711
        .distinct().limit(20).all()
    )]

    hints = []
    if final_count == 0 and teaching_users_total > 0 and school_match == 0 and assignment_match == 0:
        hints.append("Des enseignants existent mais aucun n'a users.school_id égal à l'établissement du contexte actif ni d'affectation active correspondante (voir teacher_user_school_ids). Corrigez le contexte actif (sélecteur d'établissement) ou les données.")
    if teaching_users_total == 0:
        hints.append("Aucun user actif avec un rôle enseignant (teacher/trainer/instructor). Si les lignes ont été insérées en SQL brut, vérifiez la casse du rôle : SQLAlchemy stocke le NOM de l'énumération (TEACHER), pas la valeur (teacher).")

    return {
        "active_context": {
            "organization_id": ctx.organization_id,
            "school_id": ctx.school_id,
            "school_model_assignment_id": ctx.school_model_assignment_id,
            "academic_year_id": ctx.academic_year_id,
        },
        "stages": {
            "teaching_role_users_total": teaching_users_total,
            "user_school_matches_context": school_match,
            "active_assignments_matching_context": assignment_match,
            "final_list_count": final_count,
        },
        "teacher_user_school_ids": teacher_school_ids,
        "hints": hints,
    }


@router.get("/lookup")
def lookup_teacher(
    email: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Resolve an existing teacher by email so an admin can add them to their
    school (multi-school teaching). Returns minimal identity, not full profile."""
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    teacher = db.query(models.User).join(models.TeacherProfile).filter(
        models.User.email == email.strip().lower()
    ).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Aucun enseignant trouvé avec cet email.")
    already_here = teacher_assignments.active_assignment_in_school(
        db, teacher.id, current_user.school_id
    ) is not None if current_user.school_id else False
    return {
        "id": teacher.id,
        "full_name": teacher.full_name,
        "email": teacher.email,
        "already_in_school": already_here,
    }

@router.get("/{teacher_id}", response_model=schemas.TeacherResponse)
def get_teacher(
    teacher_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    rbac.require_permission(current_user, "teachers:view", db)
    teacher = db.query(models.User).join(models.TeacherProfile).filter(
        models.User.id == teacher_id,
    ).first()
    if not teacher or not teacher_assignments.teacher_accessible(db, teacher_id, current_user):
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
    ).first()
    if not teacher or not teacher_assignments.teacher_accessible(db, teacher_id, current_user):
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
    ).first()
    if not teacher or not teacher_assignments.teacher_accessible(db, teacher_id, current_user):
        raise HTTPException(status_code=404, detail="Teacher not found")

    try:
        # Multi-school aware: a school admin removing a teacher only ends that
        # school's assignment when the teacher still teaches elsewhere. The
        # global profile/user is deleted only when this was their last school.
        caller_school_id = teacher.school_id if current_user.role == models.UserRole.SUPER_ADMIN else current_user.school_id
        active = db.query(models.TeacherAssignment).filter(
            models.TeacherAssignment.user_id == teacher_id,
            models.TeacherAssignment.is_active == True,  # noqa: E712
        ).all()
        others = [a for a in active if a.school_id != caller_school_id]
        if current_user.role != models.UserRole.SUPER_ADMIN and others:
            for assignment in active:
                if assignment.school_id == caller_school_id:
                    assignment.is_active = False
                    assignment.end_date = datetime.utcnow()
            membership = db.query(models.SchoolMembership).filter(
                models.SchoolMembership.user_id == teacher_id,
                models.SchoolMembership.school_id == caller_school_id,
                models.SchoolMembership.is_active == True,  # noqa: E712
            ).first()
            if membership:
                membership.is_active = False
                membership.membership_status = "ended"
            db.commit()
            return
        db.query(models.TeacherAssignment).filter(models.TeacherAssignment.user_id == teacher_id).delete()
        if teacher.teacher_profile:
            db.delete(teacher.teacher_profile)
        db.delete(teacher)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


def _assignment_payload(db: Session, row: models.TeacherAssignment) -> dict:
    school = db.query(models.School).filter(models.School.id == row.school_id).first()
    return {
        "id": row.id,
        "user_id": row.user_id,
        "school_id": row.school_id,
        "school_name": school.name if school else None,
        "school_model_assignment_id": row.school_model_assignment_id,
        "employment_type": row.employment_type,
        "specialization": row.specialization,
        "is_primary": row.is_primary,
        "is_active": row.is_active,
    }


@router.get("/{teacher_user_id}/assignments", response_model=List[schemas.TeacherAssignmentResponse])
def list_teacher_assignments(
    teacher_user_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "teachers:view", db)
    if not teacher_assignments.teacher_accessible(db, teacher_user_id, current_user):
        raise HTTPException(status_code=404, detail="Teacher not found")
    rows = db.query(models.TeacherAssignment).filter(
        models.TeacherAssignment.user_id == teacher_user_id
    ).order_by(models.TeacherAssignment.is_active.desc(), models.TeacherAssignment.id).all()
    return [_assignment_payload(db, row) for row in rows]


@router.post("/{teacher_user_id}/assignments", response_model=schemas.TeacherAssignmentResponse)
def add_teacher_assignment(
    teacher_user_id: int,
    payload: schemas.TeacherAssignmentCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Attach an existing teacher to the caller's active school/model context,
    additively — the teacher keeps their other schools' assignments."""
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to assign teachers")
    teacher = db.query(models.User).join(models.TeacherProfile).filter(models.User.id == teacher_user_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    active_context = school_context.resolve_context(db, current_user)
    # Additive membership: unlike a transfer, adding a second school must not end
    # the teacher's membership at their other schools.
    existing_membership = db.query(models.SchoolMembership).filter(
        models.SchoolMembership.user_id == teacher_user_id,
        models.SchoolMembership.school_id == active_context.school_id,
        models.SchoolMembership.role == models.UserRole.TEACHER.value,
        models.SchoolMembership.is_active == True,  # noqa: E712
    ).first()
    if not existing_membership:
        db.add(models.SchoolMembership(
            user_id=teacher_user_id,
            school_id=active_context.school_id,
            role=models.UserRole.TEACHER.value,
            is_active=True,
            membership_status="active",
        ))
    assignment = teacher_assignments.ensure_assignment(
        db,
        user_id=teacher_user_id,
        school_id=active_context.school_id,
        school_model_assignment_id=active_context.school_model_assignment_id,
        specialization=payload.specialization,
        employment_type=payload.employment_type,
        created_by_user_id=current_user.id,
    )
    db.commit()
    db.refresh(assignment)
    return _assignment_payload(db, assignment)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def end_teacher_assignment(
    assignment_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """End a teacher's engagement at one school without touching the others."""
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    assignment = db.query(models.TeacherAssignment).filter(models.TeacherAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if current_user.role != models.UserRole.SUPER_ADMIN and assignment.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.is_active = False
    assignment.end_date = datetime.utcnow()
    db.commit()
