from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security


router = APIRouter(prefix="/internships", tags=["Internships"])

INTERNSHIP_MANAGERS = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.DIRECTOR,
    models.UserRole.PRINCIPAL,
    models.UserRole.PEDAGOGY_COORDINATOR,
    models.UserRole.REGISTRAR,
}

INTERNSHIP_MENTORS = {
    models.UserRole.TEACHER,
    models.UserRole.TRAINER,
    models.UserRole.INSTRUCTOR,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _can_manage(current_user: models.User) -> bool:
    return current_user.role in INTERNSHIP_MANAGERS


def _can_follow_or_evaluate(current_user: models.User) -> bool:
    return current_user.role in INTERNSHIP_MANAGERS or current_user.role in INTERNSHIP_MENTORS


def _get_company(db: Session, company_id: int, current_user: models.User) -> models.PartnerCompany:
    row = db.query(models.PartnerCompany).filter(
        models.PartnerCompany.id == company_id,
        models.PartnerCompany.school_id == _school_id(current_user),
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner company not found")
    return row


def _get_internship(db: Session, internship_id: int, current_user: models.User) -> models.Internship:
    school_id = _school_id(current_user)
    row = db.query(models.Internship).filter(
        models.Internship.id == internship_id,
        models.Internship.school_id == school_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Internship not found")
    if _can_manage(current_user):
        return row
    if current_user.role in INTERNSHIP_MENTORS:
        if current_user.id in {row.teacher_ref_id, row.pedagogy_coordinator_id, row.internship_manager_id}:
            return row
    if current_user.role in {models.UserRole.STUDENT, models.UserRole.PUPIL}:
        student = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
        if student and db.query(models.InternshipAssignment).filter_by(internship_id=row.id, student_id=student.id).first():
            return row
    if current_user.role == models.UserRole.PARENT:
        linked_students = db.query(models.ParentStudentLink.student_id).filter(
            models.ParentStudentLink.parent_user_id == current_user.id,
            models.ParentStudentLink.is_active == True,
        )
        if db.query(models.InternshipAssignment).filter(
            models.InternshipAssignment.internship_id == row.id,
            models.InternshipAssignment.student_id.in_(linked_students),
        ).first():
            return row
    raise HTTPException(status_code=403, detail="Not authorized")


def _student_name(student: models.StudentProfile) -> str:
    return student.user.full_name if student.user and student.user.full_name else f"Student #{student.id}"


def _internship_scope(db: Session, current_user: models.User):
    query = db.query(models.Internship).filter(models.Internship.school_id == _school_id(current_user))
    if _can_manage(current_user):
        return query
    if current_user.role in INTERNSHIP_MENTORS:
        return query.filter(or_(
            models.Internship.teacher_ref_id == current_user.id,
            models.Internship.pedagogy_coordinator_id == current_user.id,
            models.Internship.internship_manager_id == current_user.id,
        ))
    if current_user.role in {models.UserRole.STUDENT, models.UserRole.PUPIL}:
        student = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
        if not student:
            return query.filter(models.Internship.id == -1)
        internship_ids = db.query(models.InternshipAssignment.internship_id).filter(models.InternshipAssignment.student_id == student.id)
        return query.filter(models.Internship.id.in_(internship_ids))
    if current_user.role == models.UserRole.PARENT:
        linked_students = db.query(models.ParentStudentLink.student_id).filter(
            models.ParentStudentLink.parent_user_id == current_user.id,
            models.ParentStudentLink.is_active == True,
        )
        internship_ids = db.query(models.InternshipAssignment.internship_id).filter(models.InternshipAssignment.student_id.in_(linked_students))
        return query.filter(models.Internship.id.in_(internship_ids))
    return query.filter(models.Internship.id == -1)


def _company_response(db: Session, row: models.PartnerCompany) -> schemas.PartnerCompanyResponse:
    count = db.query(func.count(models.InternshipAssignment.id)).join(
        models.Internship,
        models.Internship.id == models.InternshipAssignment.internship_id,
    ).filter(models.Internship.company_id == row.id).scalar() or 0
    payload = schemas.PartnerCompanyResponse.model_validate(row)
    payload.interns_count = int(count)
    return payload


def _internship_response(db: Session, row: models.Internship) -> schemas.InternshipResponse:
    count = db.query(func.count(models.InternshipAssignment.id)).filter(
        models.InternshipAssignment.internship_id == row.id
    ).scalar() or 0
    payload = schemas.InternshipResponse.model_validate(row)
    payload.assignments_count = int(count)
    return payload


@router.get("/dashboard/summary", response_model=schemas.InternshipDashboardResponse)
def dashboard_summary(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    school_id = _school_id(current_user)
    scoped_ids = _internship_scope(db, current_user).with_entities(models.Internship.id).subquery()
    total = db.query(func.count(models.Internship.id)).filter(models.Internship.id.in_(scoped_ids)).scalar() or 0
    active = db.query(func.count(models.Internship.id)).filter(
        models.Internship.id.in_(scoped_ids),
        models.Internship.status.in_(["planned", "in_progress"]),
    ).scalar() or 0
    completed = db.query(func.count(models.Internship.id)).filter(
        models.Internship.id.in_(scoped_ids),
        models.Internship.status.in_(["completed", "evaluated"]),
    ).scalar() or 0
    companies = db.query(func.count(models.PartnerCompany.id)).filter(models.PartnerCompany.school_id == school_id).scalar() or 0
    students = db.query(func.count(func.distinct(models.InternshipAssignment.student_id))).filter(
        models.InternshipAssignment.school_id == school_id,
        models.InternshipAssignment.internship_id.in_(scoped_ids),
    ).scalar() or 0
    evaluated = db.query(func.count(models.Internship.id)).filter(
        models.Internship.id.in_(scoped_ids),
        models.Internship.status == "evaluated",
    ).scalar() or 0
    by_company = dict(db.query(models.Internship.company_name, func.count(models.Internship.id)).filter(
        models.Internship.id.in_(scoped_ids)
    ).group_by(models.Internship.company_name).all())
    by_level = dict(db.query(models.Internship.academic_level, func.count(models.Internship.id)).filter(
        models.Internship.id.in_(scoped_ids)
    ).group_by(models.Internship.academic_level).all())
    by_country = dict(db.query(models.PartnerCompany.country, func.count(models.PartnerCompany.id)).filter(
        models.PartnerCompany.school_id == school_id
    ).group_by(models.PartnerCompany.country).all())
    return schemas.InternshipDashboardResponse(
        total_internships=int(total),
        active_internships=int(active),
        completed_internships=int(completed),
        partner_companies=int(companies),
        students_in_internship=int(students),
        validation_rate=round((evaluated / total) * 100, 2) if total else 0,
        insertion_rate=0,
        by_company={str(key or "Non renseigne"): int(value) for key, value in by_company.items()},
        by_level={str(key or "Non renseigne"): int(value) for key, value in by_level.items()},
        by_country={str(key or "Non renseigne"): int(value) for key, value in by_country.items()},
    )


@router.get("/companies", response_model=List[schemas.PartnerCompanyResponse])
def list_companies(
    q: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    query = db.query(models.PartnerCompany).filter(models.PartnerCompany.school_id == _school_id(current_user))
    if q:
        query = query.filter(models.PartnerCompany.name.ilike(f"%{q}%"))
    if status:
        query = query.filter(models.PartnerCompany.status == status)
    return [_company_response(db, row) for row in query.order_by(models.PartnerCompany.created_at.desc()).all()]


@router.post("/companies", response_model=schemas.PartnerCompanyResponse)
def create_company(
    payload: schemas.PartnerCompanyCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    row = models.PartnerCompany(**payload.model_dump(), school_id=_school_id(current_user), created_by_id=current_user.id)
    db.add(row)
    db.flush()
    audit.record_audit(db, action="internship.company.created", current_user=current_user, entity_type="partner_company", entity_id=row.id, details={"name": payload.name})
    db.commit()
    db.refresh(row)
    return _company_response(db, row)


@router.put("/companies/{company_id}", response_model=schemas.PartnerCompanyResponse)
def update_company(
    company_id: int,
    payload: schemas.PartnerCompanyUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    row = _get_company(db, company_id, current_user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_at = datetime.utcnow()
    audit.record_audit(db, action="internship.company.updated", current_user=current_user, entity_type="partner_company", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _company_response(db, row)


@router.delete("/companies/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    row = _get_company(db, company_id, current_user)
    linked = db.query(models.Internship).filter(models.Internship.company_id == row.id).first()
    if linked:
        row.status = "inactive"
        row.updated_at = datetime.utcnow()
        message = "Company has internships and was deactivated"
    else:
        db.delete(row)
        message = "Company deleted"
    audit.record_audit(db, action="internship.company.deleted", current_user=current_user, entity_type="partner_company", entity_id=company_id)
    db.commit()
    return {"message": message}


@router.get("/", response_model=List[schemas.InternshipResponse])
def list_internships(
    status: Optional[str] = None,
    company_id: Optional[int] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    query = _internship_scope(db, current_user)
    if status:
        query = query.filter(models.Internship.status == status)
    if company_id:
        query = query.filter(models.Internship.company_id == company_id)
    if class_id:
        query = query.filter(models.Internship.class_id == class_id)
    return [_internship_response(db, row) for row in query.order_by(models.Internship.created_at.desc()).all()]


@router.post("/", response_model=schemas.InternshipResponse)
def create_internship(
    payload: schemas.InternshipCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    student_ids = list(dict.fromkeys([sid for sid in ([payload.student_id] if payload.student_id else []) + payload.student_ids if sid]))
    if not student_ids:
        raise HTTPException(status_code=400, detail="At least one trainee is required")
    students = db.query(models.StudentProfile).filter(
        models.StudentProfile.id.in_(student_ids),
        models.StudentProfile.user.has(models.User.school_id == _school_id(current_user)),
    ).all()
    if len(students) != len(student_ids):
        raise HTTPException(status_code=400, detail="One or more students are invalid")
    company_name = payload.company_name
    if payload.company_id:
        company_name = _get_company(db, payload.company_id, current_user).name
    data = payload.model_dump(exclude={"student_ids"})
    data["student_id"] = student_ids[0]
    data["company_name"] = company_name
    row = models.Internship(**data, school_id=_school_id(current_user), created_by_id=current_user.id)
    db.add(row)
    db.flush()
    for student in students:
        db.add(models.InternshipAssignment(internship_id=row.id, student_id=student.id, school_id=_school_id(current_user)))
        db.add(models.NotificationHistory(
            event_type="internship.created",
            recipient_user_id=student.user_id,
            recipient_name=_student_name(student),
            channel="system",
            subject="Stage planifie",
            message=f"Stage {row.title or row.company_name} planifie.",
            student_id=student.id,
            source_type="internship",
            source_id=row.id,
            school_id=_school_id(current_user),
            created_by_id=current_user.id,
        ))
    audit.record_audit(db, action="internship.created", current_user=current_user, entity_type="internship", entity_id=row.id, details={"students": student_ids})
    db.commit()
    db.refresh(row)
    return _internship_response(db, row)


@router.put("/{internship_id}", response_model=schemas.InternshipResponse)
def update_internship(
    internship_id: int,
    payload: schemas.InternshipUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    row = _get_internship(db, internship_id, current_user)
    data = payload.model_dump(exclude_unset=True)
    if data.get("company_id"):
        data["company_name"] = _get_company(db, data["company_id"], current_user).name
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = datetime.utcnow()
    audit.record_audit(db, action="internship.updated", current_user=current_user, entity_type="internship", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _internship_response(db, row)


@router.delete("/{internship_id}")
def delete_internship(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    row = _get_internship(db, internship_id, current_user)
    if row.status in {"in_progress", "completed", "evaluated"}:
        raise HTTPException(status_code=400, detail="Protected internships cannot be deleted; cancel or suspend them")
    db.query(models.InternshipAssignment).filter(models.InternshipAssignment.internship_id == row.id).delete()
    db.delete(row)
    audit.record_audit(db, action="internship.deleted", current_user=current_user, entity_type="internship", entity_id=internship_id)
    db.commit()
    return {"message": "Internship deleted"}


@router.get("/{internship_id}/assignments", response_model=List[schemas.InternshipAssignmentResponse])
def list_assignments(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _get_internship(db, internship_id, current_user)
    rows = db.query(models.InternshipAssignment).filter(models.InternshipAssignment.internship_id == internship_id).all()
    result = []
    for row in rows:
        payload = schemas.InternshipAssignmentResponse.model_validate(row)
        payload.student_name = _student_name(row.student)
        payload.class_name = row.student.current_class.name if row.student and row.student.current_class else None
        result.append(payload)
    return result


@router.post("/followups", response_model=schemas.InternshipFollowUpResponse)
def create_followup(
    payload: schemas.InternshipFollowUpCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, payload.internship_id, current_user)
    if not _can_follow_or_evaluate(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    item = models.InternshipDailyFollowUp(**payload.model_dump(), supervisor_user_id=current_user.id, school_id=row.school_id)
    db.add(item)
    audit.record_audit(db, action="internship.followup.created", current_user=current_user, entity_type="internship", entity_id=row.id, details={"presence": payload.presence_status})
    db.commit()
    db.refresh(item)
    return item


@router.get("/{internship_id}/followups", response_model=List[schemas.InternshipFollowUpResponse])
def list_followups(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, internship_id, current_user)
    return db.query(models.InternshipDailyFollowUp).filter(models.InternshipDailyFollowUp.internship_id == row.id).order_by(models.InternshipDailyFollowUp.date.desc()).all()


@router.post("/logbook", response_model=schemas.InternshipLogbookResponse)
def create_logbook(
    payload: schemas.InternshipLogbookCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, payload.internship_id, current_user)
    if current_user.role in {models.UserRole.STUDENT, models.UserRole.PUPIL}:
        student = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
        if not student or student.id != payload.student_id:
            raise HTTPException(status_code=403, detail="Students can only update their own logbook")
    item = models.InternshipLogbookEntry(**payload.model_dump(), school_id=row.school_id)
    db.add(item)
    audit.record_audit(db, action="internship.logbook.created", current_user=current_user, entity_type="internship", entity_id=row.id)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{internship_id}/logbook", response_model=List[schemas.InternshipLogbookResponse])
def list_logbook(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, internship_id, current_user)
    return db.query(models.InternshipLogbookEntry).filter(models.InternshipLogbookEntry.internship_id == row.id).order_by(models.InternshipLogbookEntry.date.desc()).all()


@router.put("/logbook/{entry_id}/validate", response_model=schemas.InternshipLogbookResponse)
def validate_logbook(
    entry_id: int,
    payload: schemas.InternshipLogbookUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    item = db.query(models.InternshipLogbookEntry).filter(
        models.InternshipLogbookEntry.id == entry_id,
        models.InternshipLogbookEntry.school_id == _school_id(current_user),
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Logbook entry not found")
    _get_internship(db, item.internship_id, current_user)
    if not _can_follow_or_evaluate(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    item.validation_status = payload.validation_status
    item.supervisor_comment = payload.supervisor_comment
    item.validated_by_id = current_user.id
    item.validated_at = datetime.utcnow()
    audit.record_audit(db, action="internship.logbook.validated", current_user=current_user, entity_type="internship_logbook", entity_id=item.id, details={"status": payload.validation_status})
    db.commit()
    db.refresh(item)
    return item


@router.post("/evaluations", response_model=schemas.InternshipEvaluationResponse)
def create_evaluation(
    payload: schemas.InternshipEvaluationCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, payload.internship_id, current_user)
    if not _can_follow_or_evaluate(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    item = models.InternshipEvaluation(**payload.model_dump(), evaluator_id=current_user.id, school_id=row.school_id)
    if payload.final_score is not None:
        row.final_score = payload.final_score
        row.status = "evaluated"
    db.add(item)
    audit.record_audit(db, action="internship.evaluation.created", current_user=current_user, entity_type="internship", entity_id=row.id, details={"type": payload.evaluation_type, "final_score": payload.final_score})
    db.commit()
    db.refresh(item)
    return item


@router.get("/{internship_id}/evaluations", response_model=List[schemas.InternshipEvaluationResponse])
def list_evaluations(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, internship_id, current_user)
    return db.query(models.InternshipEvaluation).filter(models.InternshipEvaluation.internship_id == row.id).order_by(models.InternshipEvaluation.created_at.desc()).all()


@router.post("/documents", response_model=schemas.InternshipDocumentResponse)
def create_document(
    payload: schemas.InternshipDocumentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, payload.internship_id, current_user)
    item = models.InternshipDocument(**payload.model_dump(), school_id=row.school_id, uploaded_by_id=current_user.id)
    db.add(item)
    audit.record_audit(db, action="internship.document.created", current_user=current_user, entity_type="internship", entity_id=row.id, details={"type": payload.document_type})
    db.commit()
    db.refresh(item)
    return item


@router.get("/{internship_id}/documents", response_model=List[schemas.InternshipDocumentResponse])
def list_documents(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, internship_id, current_user)
    return db.query(models.InternshipDocument).filter(models.InternshipDocument.internship_id == row.id).order_by(models.InternshipDocument.created_at.desc()).all()


@router.post("/{internship_id}/generate-documents", response_model=List[schemas.InternshipDocumentResponse])
def generate_documents(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, internship_id, current_user)
    if not _can_manage(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    types = [
        ("attestation_stage", "Attestation de stage"),
        ("certificat_stage", "Certificat de stage"),
        ("fiche_evaluation", "Fiche d'evaluation"),
        ("rapport_synthetique", "Rapport synthetique"),
        ("releve_stage", "Releve de stage"),
        ("resultat_final", "Resultat final"),
    ]
    created = []
    for document_type, title in types:
        item = models.InternshipDocument(
            internship_id=row.id,
            document_type=document_type,
            title=title,
            status="generated",
            school_id=row.school_id,
            uploaded_by_id=current_user.id,
        )
        db.add(item)
        created.append(item)
    audit.record_audit(db, action="internship.documents.generated", current_user=current_user, entity_type="internship", entity_id=row.id)
    db.commit()
    for item in created:
        db.refresh(item)
    return created


@router.post("/{internship_id}/ai-analysis", response_model=schemas.InternshipResponse)
def ai_analysis(
    internship_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    row = _get_internship(db, internship_id, current_user)
    log_count = db.query(func.count(models.InternshipLogbookEntry.id)).filter(models.InternshipLogbookEntry.internship_id == row.id).scalar() or 0
    eval_count = db.query(func.count(models.InternshipEvaluation.id)).filter(models.InternshipEvaluation.internship_id == row.id).scalar() or 0
    row.ai_summary = (
        f"Analyse IA: stage '{row.title or row.company_name}' avec {log_count} entree(s) de journal "
        f"et {eval_count} evaluation(s). Recommandation: verifier les rapports incomplets, "
        "les competences acquises et la validation finale avant generation des attestations."
    )
    audit.record_audit(db, action="internship.ai_analysis.generated", current_user=current_user, entity_type="internship", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _internship_response(db, row)
