import csv
import io
import uuid
from datetime import datetime, time, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from .. import audit, models, pdf, schemas, security, database, tenancy
from ..services import school_context, timetable_constraints, timetable_config, timetable_optimizer, timetable_simulation, timetable_substitution

router = APIRouter(prefix="/education", tags=["Education"])


ADMIN_TIMETABLE_ROLES = {
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.SUPER_ADMIN,
    models.UserRole.ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.DIRECTOR,
    models.UserRole.PRINCIPAL,
    models.UserRole.PEDAGOGY_COORDINATOR,
}


def _require_school(current_user: models.User) -> int:
    return tenancy.require_school_scope(current_user)


def _resolve_school(current_user: models.User, payload_school_id: Optional[int], db: Session) -> int:
    return tenancy.resolve_school_id_for_create(current_user, payload_school_id, db)


def _require_timetable_admin(current_user: models.User) -> None:
    if current_user.role not in ADMIN_TIMETABLE_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return _minutes(start_a) < _minutes(end_b) and _minutes(start_b) < _minutes(end_a)


def _duration(start: time, end: time) -> int:
    return max(_minutes(end) - _minutes(start), 0)


def _scope_query(db: Session, school_id: int):
    return db.query(models.Timetable).join(models.Class).filter(models.Class.school_id == school_id)


def _entry_school_check(db: Session, school_id: int, class_id: int) -> models.Class:
    cls = db.query(models.Class).filter(models.Class.id == class_id, models.Class.school_id == school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found in this school")
    return cls


def _teacher_school_check(db: Session, school_id: int, teacher_id: Optional[int]) -> None:
    if not teacher_id:
        return
    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.school_id == school_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found in this school")


def _subject_school_check(db: Session, school_id: int, subject_id: int) -> None:
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id, models.Subject.school_id == school_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found in this school")


def _suggestions_for(entry: models.Timetable | schemas.TimetableCreate | schemas.TimetableUpdate) -> List[str]:
    suggestions = [
        "Déplacer le cours vers un créneau libre de la même journée.",
        "Choisir une autre salle compatible avec la matière.",
        "Affecter un professeur disponible sur le créneau.",
    ]
    if getattr(entry, "start_time", None) and getattr(entry, "end_time", None) and _duration(entry.start_time, entry.end_time) > 180:
        suggestions.append("Fractionner le cours en deux séances plus courtes.")
    return suggestions


def _detect_timetable_conflicts(
    db: Session,
    school_id: int,
    entry: models.Timetable | schemas.TimetableCreate,
    exclude_id: Optional[int] = None,
    constraints: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    constraints = constraints or {}
    conflicts: List[Dict[str, Any]] = []
    start_time = entry.start_time
    end_time = entry.end_time
    day = entry.day_of_week
    class_id = entry.class_id
    teacher_id = entry.teacher_id
    room = (entry.room or "").strip()

    min_start = constraints.get("min_start", "07:00")
    max_end = constraints.get("max_end", "19:00")
    max_duration = int(constraints.get("max_course_minutes", 240))
    allowed_start = time.fromisoformat(min_start)
    allowed_end = time.fromisoformat(max_end)

    if _minutes(start_time) >= _minutes(end_time):
        conflicts.append({"type": "invalid_time", "severity": "blocking", "message": "L'heure de fin doit être postérieure à l'heure de début.", "suggestions": ["Corriger les heures du cours."]})
    if _minutes(start_time) < _minutes(allowed_start) or _minutes(end_time) > _minutes(allowed_end):
        conflicts.append({"type": "time_window", "severity": "warning", "message": f"Le cours dépasse les horaires autorisés ({min_start}-{max_end}).", "suggestions": ["Choisir un créneau dans la plage autorisée."]})
    if _duration(start_time, end_time) > max_duration:
        conflicts.append({"type": "pedagogical_duration", "severity": "warning", "message": "La durée du cours dépasse la durée pédagogique maximale configurée.", "suggestions": ["Réduire la durée ou fractionner la séance."]})

    query = _scope_query(db, school_id).filter(models.Timetable.day_of_week == day)
    if exclude_id:
        query = query.filter(models.Timetable.id != exclude_id)
    for other in query.all():
        if not _overlap(start_time, end_time, other.start_time, other.end_time):
            continue
        if other.class_id == class_id:
            conflicts.append({"type": "class_conflict", "severity": "blocking", "with_entry_id": other.id, "message": "Cette classe a déjà un cours sur ce créneau.", "suggestions": _suggestions_for(entry)})
        if teacher_id and other.teacher_id == teacher_id:
            conflicts.append({"type": "teacher_conflict", "severity": "blocking", "with_entry_id": other.id, "message": "Ce professeur est déjà affecté à un autre cours sur ce créneau.", "suggestions": _suggestions_for(entry)})
        if room and other.room and other.room.strip().lower() == room.lower():
            conflicts.append({"type": "room_conflict", "severity": "blocking", "with_entry_id": other.id, "message": "Cette salle est déjà utilisée sur ce créneau.", "suggestions": _suggestions_for(entry)})

    incompatible = constraints.get("incompatible_subjects", [])
    if incompatible:
        same_day_subjects = {
            row.subject_id for row in _scope_query(db, school_id)
            .filter(models.Timetable.class_id == class_id, models.Timetable.day_of_week == day)
            .filter(models.Timetable.id != exclude_id if exclude_id else True)
            .all()
        }
        for pair in incompatible:
            if not isinstance(pair, list) or len(pair) != 2:
                continue
            if entry.subject_id in pair and any(subject in pair for subject in same_day_subjects):
                conflicts.append({"type": "pedagogical_incompatibility", "severity": "warning", "message": "Deux matières déclarées incompatibles sont planifiées le même jour.", "suggestions": ["Déplacer l'une des matières sur un autre jour."]})
                break

    # Admin-configurable rules from the database (no hard-coded pedagogy).
    for violation in timetable_constraints.evaluate(db, school_id, entry, exclude_id=exclude_id):
        conflicts.append({**violation, "suggestions": ["Ajuster le créneau pour respecter la règle configurée."]})
    return conflicts


def _apply_conflicts(entry: models.Timetable, conflicts: List[Dict[str, Any]]) -> None:
    entry.duration_minutes = _duration(entry.start_time, entry.end_time)
    entry.conflict_details = conflicts
    entry.conflict_status = "conflict" if any(item.get("severity") == "blocking" for item in conflicts) else ("warning" if conflicts else "clear")


def _record_timetable_notification(
    db: Session,
    school_id: int,
    current_user: models.User,
    entry: models.Timetable,
    event_type: str,
    message: str,
) -> None:
    recipients: list[tuple[Optional[int], Optional[int], Optional[str], Optional[str]]] = []
    if entry.teacher_id:
        recipients.append((entry.teacher_id, None, entry.teacher.full_name if entry.teacher else None, entry.teacher.email if entry.teacher else None))
    students = db.query(models.StudentProfile).join(models.User).filter(
        models.StudentProfile.current_class_id == entry.class_id,
        models.User.school_id == school_id,
    ).all()
    for student in students:
        recipients.append((student.user_id, student.id, student.user.full_name if student.user else student.parent_name, student.user.email if student.user else student.parent_email))
        if student.parent_email or student.parent_phone_e164 or student.parent_phone:
            recipients.append((None, student.id, student.parent_name, student.parent_email or student.parent_phone_e164 or student.parent_phone))
    for recipient_user_id, student_id, recipient_name, contact in recipients:
        db.add(models.NotificationHistory(
            event_type=event_type,
            recipient_user_id=recipient_user_id,
            recipient_name=recipient_name,
            recipient_contact=contact,
            channel="system",
            subject="Mise à jour de l'emploi du temps",
            message=message,
            status="recorded",
            student_id=student_id,
            source_type="timetable",
            source_id=entry.id,
            school_id=school_id,
            created_by_id=current_user.id,
        ))

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
    
    school_id = _resolve_school(current_user, class_in.school_id, db)
    active_context = school_context.resolve_context(db, current_user)
    if active_context.school_id != school_id:
        raise HTTPException(status_code=403, detail="Le contexte actif ne correspond pas a cet etablissement.")
    new_class = models.Class(
        name=class_in.name,
        level=class_in.level,
        school_id=school_id,
        school_model_assignment_id=active_context.school_model_assignment_id,
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
    school_id: Optional[int] = None,
    x_school_model_assignment_id: Optional[int] = Header(default=None, alias="X-School-Model-Assignment-ID"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = tenancy.apply_school_filter(db.query(models.Class), models.Class, current_user, school_id)
    active_context = school_context.resolve_context(
        db, current_user, school_model_assignment_id=x_school_model_assignment_id
    )
    query = query.filter(models.Class.school_model_assignment_id == active_context.school_model_assignment_id)
    classes = query.offset(skip).limit(limit).all()
    return classes


@router.get("/classes/{class_id}/roster")
def class_roster(
    class_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    cls_query = db.query(models.Class).filter(models.Class.id == class_id)
    cls = tenancy.apply_school_filter(cls_query, models.Class, current_user).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    students = db.query(models.StudentProfile).join(models.User).filter(
        models.StudentProfile.current_class_id == class_id,
        models.User.school_id == cls.school_id,
    ).all()
    rows = []
    anomalies = []
    for student in students:
        fees = db.query(models.Fee).filter(models.Fee.student_id == student.id).all()
        paid = sum(sum(payment.amount for payment in fee.payments) for fee in fees)
        expected = sum(fee.amount for fee in fees)
        row = {
            "student_id": student.id,
            "student_user_id": student.user_id,
            "full_name": student.user.full_name if student.user else None,
            "registration_number": student.registration_number,
            "parent_name": student.parent_name,
            "parent_phone": student.parent_phone,
            "expected": expected,
            "paid": paid,
            "remaining": max(expected - paid, 0),
            "has_finance_record": len(fees) > 0,
        }
        rows.append(row)
        if not fees:
            anomalies.append({**row, "reason": "Eleve en liste de classe sans fiche frais/paiement"})
    return {
        "class": {"id": cls.id, "name": cls.name, "level": cls.level},
        "students": rows,
        "anomalies": anomalies,
    }

@router.put("/classes/{class_id}", response_model=schemas.ClassResponse)
def update_class(
    class_id: int,
    class_in: schemas.ClassCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    cls_query = db.query(models.Class).filter(models.Class.id == class_id)
    cls = tenancy.apply_school_filter(cls_query, models.Class, current_user).first()
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    active_context = school_context.resolve_context(db, current_user)
    if cls.school_model_assignment_id != active_context.school_model_assignment_id:
        raise HTTPException(status_code=404, detail="Classe introuvable dans le contexte actif.")
    if cls.is_system_default and cls.name != class_in.name:
        raise HTTPException(status_code=409, detail="Le nom d'une classe systeme ne peut pas etre modifie.")
        
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

    cls_query = db.query(models.Class).filter(models.Class.id == class_id)
    cls = tenancy.apply_school_filter(cls_query, models.Class, current_user).first()
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    active_context = school_context.resolve_context(db, current_user)
    if cls.school_model_assignment_id != active_context.school_model_assignment_id:
        raise HTTPException(status_code=404, detail="Classe introuvable dans le contexte actif.")
    if cls.is_system_default:
        raise HTTPException(status_code=409, detail="Une classe systeme ne peut pas etre supprimee.")
        
    db.delete(cls)
    db.commit()

# ---------------------------------------------------------
# Years & Terms Endpoints
# ---------------------------------------------------------

@router.get("/academic-years", response_model=List[schemas.AcademicYearResponse])
def list_academic_years(
    skip: int = 0,
    limit: int = 100,
    current_only: bool = False,
    school_id: Optional[int] = None,
    x_school_model_assignment_id: Optional[int] = Header(default=None, alias="X-School-Model-Assignment-ID"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = tenancy.apply_school_filter(db.query(models.AcademicYear), models.AcademicYear, current_user, school_id)
    active_context = school_context.resolve_context(
        db, current_user, school_model_assignment_id=x_school_model_assignment_id
    )
    query = query.filter(models.AcademicYear.school_model_assignment_id == active_context.school_model_assignment_id)
    if current_only:
        query = query.filter(models.AcademicYear.is_current == True)

    return query.order_by(models.AcademicYear.start_date.desc().nullslast(), models.AcademicYear.id.desc()).offset(skip).limit(limit).all()

@router.get("/terms", response_model=List[schemas.TermResponse])
def list_terms(
    academic_year_id: int = None,
    school_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Term).join(models.AcademicYear)
    query = tenancy.apply_school_filter(query, models.AcademicYear, current_user, school_id)
    if academic_year_id:
        query = query.filter(models.Term.academic_year_id == academic_year_id)

    return query.order_by(models.Term.start_date.asc().nullslast(), models.Term.id.asc()).offset(skip).limit(limit).all()

@router.post("/academic-years", response_model=schemas.AcademicYearResponse)
def create_academic_year(
    year_in: schemas.AcademicYearCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    school_id = _resolve_school(current_user, year_in.school_id, db)
    active_context = school_context.resolve_context(db, current_user)
    new_year = models.AcademicYear(
        **year_in.model_dump(exclude={"school_id"}),
        school_id=school_id,
        school_model_assignment_id=active_context.school_model_assignment_id,
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
        
    academic_year_query = db.query(models.AcademicYear).filter(models.AcademicYear.id == term_in.academic_year_id)
    academic_year = tenancy.apply_school_filter(academic_year_query, models.AcademicYear, current_user).first()
    if not academic_year:
        raise HTTPException(status_code=404, detail="Academic year not found in this school")

    new_term = models.Term(**term_in.model_dump())
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
        
    school_id = _resolve_school(current_user, subject_in.school_id, db)
    active_context = school_context.resolve_context(db, current_user)
    new_sub = models.Subject(
        **subject_in.model_dump(exclude={"school_id"}),
        school_id=school_id,
        school_model_assignment_id=active_context.school_model_assignment_id,
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.get("/subjects", response_model=List[schemas.SubjectResponse])
def list_subjects(
    skip: int = 0,
    limit: int = 100,
    school_id: Optional[int] = None,
    x_school_model_assignment_id: Optional[int] = Header(default=None, alias="X-School-Model-Assignment-ID"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = tenancy.apply_school_filter(db.query(models.Subject), models.Subject, current_user, school_id)
    active_context = school_context.resolve_context(
        db, current_user, school_model_assignment_id=x_school_model_assignment_id
    )
    query = query.filter(models.Subject.school_model_assignment_id == active_context.school_model_assignment_id)
    subjects = query.offset(skip).limit(limit).all()
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

    sub_query = db.query(models.Subject).filter(models.Subject.id == subject_id)
    sub = tenancy.apply_school_filter(sub_query, models.Subject, current_user).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")
    active_context = school_context.resolve_context(db, current_user)
    if sub.school_model_assignment_id != active_context.school_model_assignment_id:
        raise HTTPException(status_code=404, detail="Matiere introuvable dans le contexte actif.")
    if sub.is_system_default and subject_in.name is not None and subject_in.name != sub.name:
        raise HTTPException(status_code=409, detail="Le nom d'une matiere systeme ne peut pas etre modifie.")
        
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

    sub_query = db.query(models.Subject).filter(models.Subject.id == subject_id)
    sub = tenancy.apply_school_filter(sub_query, models.Subject, current_user).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")
    active_context = school_context.resolve_context(db, current_user)
    if sub.school_model_assignment_id != active_context.school_model_assignment_id:
        raise HTTPException(status_code=404, detail="Matiere introuvable dans le contexte actif.")
    if sub.is_system_default:
        raise HTTPException(status_code=409, detail="Une matiere systeme ne peut pas etre supprimee.")
        
    db.delete(sub)
    db.commit()


# ---------------------------------------------------------
# Timetables endpoints
# ---------------------------------------------------------

def _school_id_from_class(db: Session, class_id: int) -> int:
    cls = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls.school_id


def _timetable_query_for_user(db: Session, current_user: models.User, school_id: Optional[int] = None):
    if current_user.role == models.UserRole.SUPER_ADMIN:
        query = db.query(models.Timetable).join(models.Class)
        if school_id:
            query = query.filter(models.Class.school_id == school_id)
    else:
        school_id = _require_school(current_user)
        query = _scope_query(db, school_id)
    if current_user.role in [models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR]:
        return query.filter(models.Timetable.teacher_id == current_user.id, models.Timetable.status == "published")
    if current_user.role in [models.UserRole.STUDENT, models.UserRole.PUPIL]:
        if not current_user.student_profile or not current_user.student_profile.current_class_id:
            return query.filter(False)
        return query.filter(models.Timetable.class_id == current_user.student_profile.current_class_id, models.Timetable.status == "published")
    if current_user.role == models.UserRole.PARENT:
        students = db.query(models.StudentProfile).join(models.User).filter(
            models.User.school_id == school_id,
            models.StudentProfile.parent_email == current_user.email,
        ).all()
        class_ids = [student.current_class_id for student in students if student.current_class_id]
        return query.filter(models.Timetable.class_id.in_(class_ids), models.Timetable.status == "published") if class_ids else query.filter(False)
    return query


@router.post("/timetables", response_model=schemas.TimetableResponse)
def create_timetable_entry(
    entry_in: schemas.TimetableCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _require_timetable_admin(current_user)
    school_id = _school_id_from_class(db, entry_in.class_id) if current_user.role == models.UserRole.SUPER_ADMIN else _require_school(current_user)
    _entry_school_check(db, school_id, entry_in.class_id)
    _subject_school_check(db, school_id, entry_in.subject_id)
    _teacher_school_check(db, school_id, entry_in.teacher_id)
    entry = models.Timetable(**entry_in.model_dump())
    conflicts = _detect_timetable_conflicts(db, school_id, entry, constraints=entry_in.constraints_snapshot)
    _apply_conflicts(entry, conflicts)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    audit.record_audit(db, action="timetable.entry.created", current_user=current_user, entity_type="timetable", entity_id=entry.id, details={"conflicts": conflicts})
    return entry


@router.get("/timetables", response_model=List[schemas.TimetableResponse])
def list_timetables(
    class_id: int = None,
    teacher_id: int = None,
    room: str = None,
    status_filter: str = None,
    school_id: Optional[int] = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    query = _timetable_query_for_user(db, current_user, school_id)
    if class_id:
        query = query.filter(models.Timetable.class_id == class_id)
    if teacher_id:
        query = query.filter(models.Timetable.teacher_id == teacher_id)
    if room:
        query = query.filter(models.Timetable.room == room)
    if status_filter:
        query = query.filter(models.Timetable.status == status_filter)
    return query.order_by(models.Timetable.day_of_week, models.Timetable.start_time).all()


@router.put("/timetables/{entry_id}", response_model=schemas.TimetableResponse)
def update_timetable_entry(
    entry_id: int,
    entry_in: schemas.TimetableUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _require_timetable_admin(current_user)
    if current_user.role == models.UserRole.SUPER_ADMIN:
        entry = db.query(models.Timetable).join(models.Class).filter(models.Timetable.id == entry_id).first()
        school_id = entry.class_.school_id if entry and entry.class_ else None
    else:
        school_id = _require_school(current_user)
        entry = _scope_query(db, school_id).filter(models.Timetable.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    changes = entry_in.model_dump(exclude_unset=True)
    _entry_school_check(db, school_id, changes.get("class_id", entry.class_id))
    _subject_school_check(db, school_id, changes.get("subject_id", entry.subject_id))
    _teacher_school_check(db, school_id, changes.get("teacher_id", entry.teacher_id))
    for key, value in changes.items():
        setattr(entry, key, value)
    conflicts = _detect_timetable_conflicts(db, school_id, entry, exclude_id=entry.id, constraints=entry.constraints_snapshot)
    _apply_conflicts(entry, conflicts)
    if entry.status == "published":
        entry.status = "draft"
    db.commit()
    db.refresh(entry)
    _record_timetable_notification(db, school_id, current_user, entry, "timetable.updated", "Un cours de votre emploi du temps a été modifié.")
    audit.record_audit(db, action="timetable.entry.updated", current_user=current_user, entity_type="timetable", entity_id=entry.id, details={"changes": changes, "conflicts": conflicts})
    db.commit()
    return entry


@router.post("/timetables/bulk-update")
def bulk_update_timetables(
    payload: schemas.TimetableBulkUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _require_timetable_admin(current_user)
    first_entry = db.query(models.Timetable).join(models.Class).filter(models.Timetable.id.in_(payload.entry_ids)).first()
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if not first_entry or not first_entry.class_:
            raise HTTPException(status_code=404, detail="Timetable entry not found")
        school_id = first_entry.class_.school_id
    else:
        school_id = _require_school(current_user)
    updated: List[int] = []
    conflicts_by_entry: Dict[int, List[Dict[str, Any]]] = {}
    for entry_id in payload.entry_ids:
        entry = _scope_query(db, school_id).filter(models.Timetable.id == entry_id).first()
        if not entry:
            continue
        changes = payload.changes.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entry, key, value)
        conflicts = _detect_timetable_conflicts(db, school_id, entry, exclude_id=entry.id, constraints=entry.constraints_snapshot)
        _apply_conflicts(entry, conflicts)
        updated.append(entry.id)
        conflicts_by_entry[entry.id] = conflicts
    db.commit()
    audit.record_audit(db, action="timetable.entries.bulk_updated", current_user=current_user, entity_type="timetable", details={"entry_ids": updated, "conflicts": conflicts_by_entry})
    return {"updated": updated, "conflicts": conflicts_by_entry}


@router.post("/timetables/validate")
def validate_timetable_entry(
    entry_in: schemas.TimetableCreate,
    exclude_id: int = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _require_timetable_admin(current_user)
    school_id = _school_id_from_class(db, entry_in.class_id) if current_user.role == models.UserRole.SUPER_ADMIN else _require_school(current_user)
    _entry_school_check(db, school_id, entry_in.class_id)
    _subject_school_check(db, school_id, entry_in.subject_id)
    _teacher_school_check(db, school_id, entry_in.teacher_id)
    conflicts = _detect_timetable_conflicts(db, school_id, entry_in, exclude_id=exclude_id, constraints=entry_in.constraints_snapshot)
    return {"has_conflicts": bool(conflicts), "conflicts": conflicts, "suggestions": _suggestions_for(entry_in)}


def _delete_unlocked_for_generation(db: Session, school_id: int, payload: schemas.TimetableGenerationRequest) -> int:
    query = _scope_query(db, school_id)
    if payload.preserve_locks:
        query = query.filter(models.Timetable.is_locked == False)
    if payload.scope_type == "class" and payload.scope_id:
        query = query.filter(models.Timetable.class_id == payload.scope_id)
    elif payload.scope_type == "teacher" and payload.scope_id:
        query = query.filter(models.Timetable.teacher_id == payload.scope_id)
    elif payload.scope_type == "level" and payload.level:
        query = query.filter(models.Class.level == payload.level)
    elif payload.scope_type == "subject" and payload.subject_ids:
        query = query.filter(models.Timetable.subject_id.in_(payload.subject_ids))
    elif payload.mode != "complete":
        return 0
    rows = query.all()
    for row in rows:
        db.delete(row)
    db.flush()
    return len(rows)


@router.post("/timetables/generate")
def generate_timetables(
    payload: schemas.TimetableGenerationRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _require_timetable_admin(current_user)
    school_id = tenancy.resolve_school_id_for_create(current_user, payload.school_id, db) if current_user.role == models.UserRole.SUPER_ADMIN else _require_school(current_user)
    deleted = _delete_unlocked_for_generation(db, school_id, payload)
    classes_query = db.query(models.Class).filter(models.Class.school_id == school_id)
    if payload.scope_type == "class" and payload.scope_id:
        classes_query = classes_query.filter(models.Class.id == payload.scope_id)
    if payload.scope_type == "level" and payload.level:
        classes_query = classes_query.filter(models.Class.level == payload.level)
    classes = classes_query.order_by(models.Class.level, models.Class.name).all()
    subject_query = db.query(models.Subject).filter(models.Subject.school_id == school_id)
    if payload.subject_ids:
        subject_query = subject_query.filter(models.Subject.id.in_(payload.subject_ids))
    subjects = subject_query.order_by(models.Subject.name).all()
    teachers = db.query(models.User).filter(
        models.User.school_id == school_id,
        models.User.role.in_([models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR]),
    ).order_by(models.User.id).all()
    # Configurable grid: working days and course slots come from TimetableConfig
    # (or defaults), never hard-coded.
    working_days, course_slots = timetable_config.effective_grid(db, school_id)
    days = [models.DayOfWeek(day) for day in working_days if day in models.DayOfWeek._value2member_map_]
    slots = course_slots
    rooms = payload.constraints.get("rooms") or ["Salle 1", "Salle 2", "Salle 3", "Laboratoire 1", "Atelier 1"]
    batch = f"TT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    created: List[int] = []
    skipped: List[Dict[str, Any]] = []
    cursor = 0
    if not days or not slots:
        db.commit()
        return {"batch": batch, "created": 0, "deleted": deleted, "skipped": [{"reason": "Aucune grille horaire configurée."}], "mode": payload.mode}
    for cls in classes:
        for subject_index, subject in enumerate(subjects[: min(len(subjects), 12)]):
            # Configurable weekly volume per subject (per class, then level, then 1).
            sessions = timetable_config.weekly_sessions_for(db, school_id, subject.id, cls.id, cls.level, default=1)
            for _ in range(sessions):
                placed = False
                attempts = 0
                while attempts < len(days) * len(slots):
                    day = days[(cursor + attempts) % len(days)]
                    start, end = slots[((cursor + attempts) // len(days)) % len(slots)]
                    teacher = teachers[(subject_index + attempts) % len(teachers)] if teachers else None
                    room = rooms[(cls.id + subject_index + attempts) % len(rooms)]
                    candidate = models.Timetable(
                        day_of_week=day,
                        start_time=start,
                        end_time=end,
                        room=room,
                        class_id=cls.id,
                        subject_id=subject.id,
                        teacher_id=teacher.id if teacher else cls.main_teacher_id,
                        status="draft",
                        generation_batch=batch,
                        constraints_snapshot=payload.constraints,
                    )
                    conflicts = _detect_timetable_conflicts(db, school_id, candidate, constraints=payload.constraints)
                    if not any(item.get("severity") == "blocking" for item in conflicts):
                        _apply_conflicts(candidate, conflicts)
                        db.add(candidate)
                        db.flush()
                        created.append(candidate.id)
                        cursor += 1
                        placed = True
                        break
                    attempts += 1
                if not placed:
                    skipped.append({"class_id": cls.id, "subject_id": subject.id, "reason": "Aucun créneau sans conflit trouvé."})
    db.commit()
    audit.record_audit(db, action="timetable.generated", current_user=current_user, entity_type="timetable", details={"batch": batch, "created": len(created), "deleted": deleted, "skipped": skipped})
    return {"batch": batch, "created": len(created), "deleted": deleted, "skipped": skipped, "mode": payload.mode}


@router.post("/timetables/publish")
def publish_timetables(
    payload: schemas.TimetablePublishRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _require_timetable_admin(current_user)
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if payload.school_id:
            school_id = tenancy.resolve_school_id_for_create(current_user, payload.school_id, db)
        elif payload.class_id:
            school_id = _school_id_from_class(db, payload.class_id)
        elif payload.teacher_id:
            teacher = db.query(models.User).filter(models.User.id == payload.teacher_id).first()
            if not teacher or not teacher.school_id:
                raise HTTPException(status_code=404, detail="Teacher not found in a school")
            school_id = teacher.school_id
        else:
            raise HTTPException(status_code=400, detail=tenancy.SUPER_ADMIN_SELECT_SCHOOL_MESSAGE)
    else:
        school_id = _require_school(current_user)
    query = _scope_query(db, school_id)
    if payload.class_id:
        query = query.filter(models.Timetable.class_id == payload.class_id)
    if payload.teacher_id:
        query = query.filter(models.Timetable.teacher_id == payload.teacher_id)
    if payload.level:
        query = query.filter(models.Class.level == payload.level)
    rows = query.all()
    published = 0
    now = datetime.now(timezone.utc)
    for entry in rows:
        conflicts = _detect_timetable_conflicts(db, school_id, entry, exclude_id=entry.id, constraints=entry.constraints_snapshot)
        _apply_conflicts(entry, conflicts)
        if entry.conflict_status == "conflict":
            continue
        entry.status = "published"
        entry.published_at = now
        published += 1
        _record_timetable_notification(db, school_id, current_user, entry, "timetable.published", "Un emploi du temps validé est disponible dans votre tableau de bord.")
    db.commit()
    audit.record_audit(db, action="timetable.published", current_user=current_user, entity_type="timetable", details={"published": published, "total_checked": len(rows)})
    return {"published": published, "total_checked": len(rows)}


@router.get("/timetables/my", response_model=List[schemas.TimetableResponse])
def my_timetable(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    return _timetable_query_for_user(db, current_user).order_by(models.Timetable.day_of_week, models.Timetable.start_time).all()


@router.get("/timetables/export")
def export_timetables(
    export_format: str = "csv",
    class_id: int = None,
    teacher_id: int = None,
    room: str = None,
    school_id: Optional[int] = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        school_id = _require_school(current_user)
    query = _timetable_query_for_user(db, current_user, school_id)
    if class_id:
        query = query.filter(models.Timetable.class_id == class_id)
    if teacher_id:
        query = query.filter(models.Timetable.teacher_id == teacher_id)
    if room:
        query = query.filter(models.Timetable.room == room)
    rows = query.order_by(models.Timetable.day_of_week, models.Timetable.start_time).all()
    school = db.query(models.School).filter(models.School.id == school_id).first() if school_id else None
    headers = ["Jour", "Début", "Fin", "Classe", "Matière", "Professeur", "Salle", "Statut", "Conflits"]
    data = [[
        row.day_of_week.value,
        row.start_time.strftime("%H:%M"),
        row.end_time.strftime("%H:%M"),
        row.class_.name if row.class_ else "",
        row.subject.name if row.subject else "",
        row.teacher.full_name if row.teacher else "",
        row.room or "",
        row.status,
        row.conflict_status,
    ] for row in rows]
    if export_format == "pdf":
        lines = [f"Etablissement: {school.name if school else '-'}", f"Total cours: {len(rows)}"]
        lines.extend([" | ".join(map(str, row)) for row in data[:80]])
        from ..services import school_documents
        return Response(pdf.professional_pdf("Emploi du temps", lines, f"TIMETABLE:{school_id}:{len(rows)}", school_header=school_documents.document_header(db, school)), media_type="application/pdf")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([school.name if school else "TeducAI"])
    writer.writerow(headers)
    writer.writerows(data)
    media_type = "text/csv"
    extension = "csv"
    if export_format in {"excel", "xlsx"}:
        media_type = "application/vnd.ms-excel"
        extension = "xls"
    return Response(output.getvalue(), media_type=media_type, headers={"Content-Disposition": f"attachment; filename=timetable.{extension}"})


@router.delete("/timetables/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable_entry(
    entry_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _require_timetable_admin(current_user)
    if current_user.role == models.UserRole.SUPER_ADMIN:
        entry = db.query(models.Timetable).join(models.Class).filter(models.Timetable.id == entry_id).first()
        school_id = entry.class_.school_id if entry and entry.class_ else None
    else:
        school_id = _require_school(current_user)
        entry = _scope_query(db, school_id).filter(models.Timetable.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    _record_timetable_notification(db, school_id, current_user, entry, "timetable.deleted", "Un cours a été supprimé de votre emploi du temps.")
    audit.record_audit(db, action="timetable.entry.deleted", current_user=current_user, entity_type="timetable", entity_id=entry.id)
    db.delete(entry)
    db.commit()


# ---------------------------------------------------------------------------
# Configurable timetable constraint rules (admin-managed, no hard-coded pedagogy)
# ---------------------------------------------------------------------------

def _constraint_rule_or_404(db: Session, rule_id: int, school_id: int) -> models.TimetableConstraintRule:
    row = db.query(models.TimetableConstraintRule).filter(
        models.TimetableConstraintRule.id == rule_id,
        models.TimetableConstraintRule.school_id == school_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Constraint rule not found")
    return row


@router.get("/timetables/constraint-rule-types")
def timetable_constraint_rule_types(current_user: models.User = Depends(security.get_current_user)):
    _require_timetable_admin(current_user)
    return {"rule_types": timetable_constraints.SUPPORTED_RULE_TYPES}


@router.get("/timetables/constraint-rules", response_model=List[schemas.TimetableConstraintRuleResponse])
def list_constraint_rules(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    return db.query(models.TimetableConstraintRule).filter(
        models.TimetableConstraintRule.school_id == resolved,
    ).order_by(models.TimetableConstraintRule.rule_type, models.TimetableConstraintRule.id).all()


@router.post("/timetables/constraint-rules", response_model=schemas.TimetableConstraintRuleResponse)
def create_constraint_rule(
    payload: schemas.TimetableConstraintRuleCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    if payload.rule_type not in timetable_constraints.SUPPORTED_RULE_TYPES:
        raise HTTPException(status_code=400, detail={"unsupported_rule_type": payload.rule_type, "supported": timetable_constraints.SUPPORTED_RULE_TYPES})
    if payload.severity not in {"blocking", "warning"}:
        raise HTTPException(status_code=400, detail="severity must be 'blocking' or 'warning'")
    row = models.TimetableConstraintRule(
        school_id=resolved,
        school_model_assignment_id=payload.school_model_assignment_id,
        rule_type=payload.rule_type,
        name=payload.name,
        parameters=payload.parameters or {},
        severity=payload.severity,
        is_active=payload.is_active,
        created_by_id=current_user.id,
    )
    db.add(row)
    db.flush()
    audit.record_audit(db, action="timetable.constraint_rule.created", current_user=current_user, entity_type="timetable_constraint_rule", entity_id=row.id, details={"rule_type": row.rule_type})
    db.commit()
    db.refresh(row)
    return row


@router.put("/timetables/constraint-rules/{rule_id}", response_model=schemas.TimetableConstraintRuleResponse)
def update_constraint_rule(
    rule_id: int,
    payload: schemas.TimetableConstraintRuleUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    row = _constraint_rule_or_404(db, rule_id, resolved)
    updates = payload.model_dump(exclude_unset=True)
    if "rule_type" in updates and updates["rule_type"] not in timetable_constraints.SUPPORTED_RULE_TYPES:
        raise HTTPException(status_code=400, detail={"unsupported_rule_type": updates["rule_type"], "supported": timetable_constraints.SUPPORTED_RULE_TYPES})
    if "severity" in updates and updates["severity"] not in {"blocking", "warning"}:
        raise HTTPException(status_code=400, detail="severity must be 'blocking' or 'warning'")
    for key, value in updates.items():
        setattr(row, key, value)
    audit.record_audit(db, action="timetable.constraint_rule.updated", current_user=current_user, entity_type="timetable_constraint_rule", entity_id=row.id, details={"fields": sorted(updates.keys())})
    db.commit()
    db.refresh(row)
    return row


@router.delete("/timetables/constraint-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_constraint_rule(
    rule_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    row = _constraint_rule_or_404(db, rule_id, resolved)
    db.delete(row)
    audit.record_audit(db, action="timetable.constraint_rule.deleted", current_user=current_user, entity_type="timetable_constraint_rule", entity_id=rule_id)
    db.commit()


# ---------------------------------------------------------------------------
# Configurable timetable grid: config (days/slots), holidays, subject volume
# ---------------------------------------------------------------------------

@router.get("/timetables/config", response_model=schemas.TimetableConfigResponse)
def get_timetable_config(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    row = timetable_config.active_config(db, resolved)
    if row:
        return row
    # Return the effective defaults (not yet persisted) so the UI can show them.
    return schemas.TimetableConfigResponse(
        id=0, school_id=resolved, school_model_assignment_id=None,
        working_days=timetable_config.DEFAULT_WORKING_DAYS, slots=timetable_config.DEFAULT_SLOTS, is_active=True,
    )


@router.put("/timetables/config", response_model=schemas.TimetableConfigResponse)
def upsert_timetable_config(payload: schemas.TimetableConfigUpsert, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    row = db.query(models.TimetableConfig).filter(
        models.TimetableConfig.school_id == resolved,
        models.TimetableConfig.school_model_assignment_id == payload.school_model_assignment_id,
    ).first()
    slots = [slot.model_dump() for slot in payload.slots]
    if not row:
        row = models.TimetableConfig(school_id=resolved, school_model_assignment_id=payload.school_model_assignment_id, created_by_id=current_user.id)
        db.add(row)
    row.working_days = [day.lower() for day in payload.working_days]
    row.slots = slots
    row.is_active = payload.is_active
    audit.record_audit(db, action="timetable.config.updated", current_user=current_user, entity_type="timetable_config")
    db.commit()
    db.refresh(row)
    return row


@router.get("/timetables/holidays", response_model=List[schemas.SchoolHolidayResponse])
def list_holidays(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    return db.query(models.SchoolHoliday).filter(models.SchoolHoliday.school_id == resolved).order_by(models.SchoolHoliday.date).all()


@router.post("/timetables/holidays", response_model=schemas.SchoolHolidayResponse)
def create_holiday(payload: schemas.SchoolHolidayCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    row = models.SchoolHoliday(school_id=resolved, date=payload.date, name=payload.name)
    db.add(row)
    audit.record_audit(db, action="timetable.holiday.created", current_user=current_user, entity_type="school_holiday")
    db.commit()
    db.refresh(row)
    return row


@router.delete("/timetables/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(holiday_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    row = db.query(models.SchoolHoliday).filter(models.SchoolHoliday.id == holiday_id, models.SchoolHoliday.school_id == resolved).first()
    if not row:
        raise HTTPException(status_code=404, detail="Holiday not found")
    db.delete(row)
    db.commit()


@router.get("/timetables/subject-requirements", response_model=List[schemas.SubjectRequirementResponse])
def list_subject_requirements(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    return db.query(models.SubjectRequirement).filter(models.SubjectRequirement.school_id == resolved).order_by(models.SubjectRequirement.subject_id).all()


@router.post("/timetables/subject-requirements", response_model=schemas.SubjectRequirementResponse)
def create_subject_requirement(payload: schemas.SubjectRequirementCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    if not db.query(models.Subject.id).filter(models.Subject.id == payload.subject_id, models.Subject.school_id == resolved).first():
        raise HTTPException(status_code=404, detail="Subject not found")
    row = models.SubjectRequirement(school_id=resolved, **payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="timetable.subject_requirement.created", current_user=current_user, entity_type="subject_requirement")
    db.commit()
    db.refresh(row)
    return row


@router.delete("/timetables/subject-requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_requirement(requirement_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    row = db.query(models.SubjectRequirement).filter(models.SubjectRequirement.id == requirement_id, models.SubjectRequirement.school_id == resolved).first()
    if not row:
        raise HTTPException(status_code=404, detail="Requirement not found")
    db.delete(row)
    db.commit()


# ---------------------------------------------------------------------------
# Optimiser: several scored candidate timetables + commit a chosen one
# ---------------------------------------------------------------------------

def _serialize_candidate(candidate) -> Dict[str, Any]:
    return {
        "seed": candidate.seed,
        "score": candidate.score,
        "breakdown": candidate.breakdown,
        "unplaced": candidate.unplaced,
        "placements": [
            {
                "class_id": p.class_id,
                "subject_id": p.subject_id,
                "teacher_id": p.teacher_id,
                "day": p.day,
                "start": p.start.isoformat(),
                "end": p.end.isoformat(),
            }
            for p in candidate.placements
        ],
    }


@router.post("/timetables/optimize")
def optimize_timetables(
    payload: schemas.TimetableOptimizeRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    candidates = timetable_optimizer.generate_candidates(db, resolved, candidate_count=payload.candidate_count)
    return {"candidates": [_serialize_candidate(c) for c in candidates]}


@router.post("/timetables/optimize/commit")
def commit_optimized_timetable(
    payload: schemas.TimetableOptimizeCommit,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    candidates = timetable_optimizer.generate_candidates(db, resolved, candidate_count=payload.candidate_count)
    chosen = next((c for c in candidates if c.seed == payload.seed), None)
    if not chosen:
        raise HTTPException(status_code=404, detail="Candidate not found for the given seed")
    # Clear existing draft entries (respecting locks) before persisting the choice.
    query = _scope_query(db, resolved)
    if payload.preserve_locks:
        query = query.filter(models.Timetable.is_locked == False)  # noqa: E712
    deleted = 0
    for row in query.all():
        db.delete(row)
        deleted += 1
    db.flush()
    batch = f"OPT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    created = 0
    for placement in chosen.placements:
        db.add(models.Timetable(
            day_of_week=models.DayOfWeek(placement.day),
            start_time=placement.start,
            end_time=placement.end,
            class_id=placement.class_id,
            subject_id=placement.subject_id,
            teacher_id=placement.teacher_id,
            status="draft",
            generation_batch=batch,
        ))
        created += 1
    audit.record_audit(db, action="timetable.optimized_committed", current_user=current_user, entity_type="timetable", details={"batch": batch, "seed": chosen.seed, "score": chosen.score, "created": created, "deleted": deleted})
    db.commit()
    return {"batch": batch, "seed": chosen.seed, "score": chosen.score, "created": created, "deleted": deleted}


# ---------------------------------------------------------------------------
# Explainable AI + what-if simulation
# ---------------------------------------------------------------------------

@router.post("/timetables/explain")
def explain_best_timetable(
    payload: schemas.TimetableOptimizeRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    candidates = timetable_optimizer.generate_candidates(db, resolved, candidate_count=payload.candidate_count)
    if not candidates:
        return {"explanation": ["Aucune grille horaire configurée."], "score": 0}
    best = candidates[0]
    return {"seed": best.seed, "score": best.score, "breakdown": best.breakdown, "explanation": timetable_simulation.explain_candidate(best)}


@router.post("/timetables/simulate")
def simulate_timetable_scenario(
    payload: schemas.TimetableSimulateRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
    school_id: Optional[int] = None,
):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    result = timetable_simulation.simulate(db, resolved, payload.scenario, payload.params)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Absences, substitutions and dynamic replanning
# ---------------------------------------------------------------------------

@router.get("/timetables/absences", response_model=List[schemas.TeacherAbsenceResponse])
def list_absences(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    return db.query(models.TeacherAbsence).filter(models.TeacherAbsence.school_id == resolved).order_by(models.TeacherAbsence.start_date.desc()).all()


@router.post("/timetables/absences", response_model=schemas.TeacherAbsenceResponse)
def create_absence(payload: schemas.TeacherAbsenceCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    if not db.query(models.User.id).filter(models.User.id == payload.teacher_id, models.User.school_id == resolved).first():
        raise HTTPException(status_code=404, detail="Teacher not found")
    row = models.TeacherAbsence(school_id=resolved, created_by_id=current_user.id, **payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="timetable.absence.created", current_user=current_user, entity_type="teacher_absence", details={"teacher_id": payload.teacher_id})
    db.commit()
    db.refresh(row)
    return row


@router.get("/timetables/substitutions")
def get_substitutions(teacher_id: int, day: str, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    return {"proposals": timetable_substitution.propose_substitutions(db, resolved, teacher_id, day)}


@router.post("/timetables/substitutions/apply", response_model=schemas.TimetableResponse)
def apply_substitution(payload: schemas.SubstitutionApply, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _require_timetable_admin(current_user)
    resolved = _resolve_school(current_user, school_id, db)
    entry = _scope_query(db, resolved).filter(models.Timetable.id == payload.timetable_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    if not db.query(models.User.id).filter(models.User.id == payload.substitute_teacher_id, models.User.school_id == resolved).first():
        raise HTTPException(status_code=404, detail="Substitute teacher not found")
    # The substitute must be free at that day/slot.
    clash = _scope_query(db, resolved).filter(
        models.Timetable.id != entry.id,
        models.Timetable.teacher_id == payload.substitute_teacher_id,
        models.Timetable.day_of_week == entry.day_of_week,
    ).all()
    for other in clash:
        if _overlap(entry.start_time, entry.end_time, other.start_time, other.end_time):
            raise HTTPException(status_code=409, detail="Substitute is already booked on this slot")
    entry.teacher_id = payload.substitute_teacher_id
    audit.record_audit(db, action="timetable.substitution.applied", current_user=current_user, entity_type="timetable", entity_id=entry.id, details={"substitute_teacher_id": payload.substitute_teacher_id})
    db.commit()
    db.refresh(entry)
    return entry
