"""Staff automations hub — endpoints that trigger the platform's automation
runs (unpaid-fee reminders, parent digests, …). No background worker is
required: each run is idempotent (anti-spam tracking) so it can be triggered
manually from the Automations page or by an external cron hitting the endpoint.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security
from datetime import datetime

from ..services import absence_followup, anomaly_digest, automation, fee_reminders, grade_explainer, grade_ocr, parent_digest, remediation, rentree, sequence_builder, student_planner

router = APIRouter(prefix="/automations", tags=["Automations"])

ADMIN_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.ACCOUNTANT, models.UserRole.DIRECTION)
RENTREE_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION)
EDUCATOR_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION, models.UserRole.TEACHER)


def _ensure_admin(current_user: models.User) -> None:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Réservé à l'administration.")


def _ensure_rentree_admin(current_user: models.User) -> None:
    if current_user.role not in RENTREE_ROLES:
        raise HTTPException(status_code=403, detail="Réservé à la direction de l'établissement.")


def _school_id(current_user: models.User, school_id: Optional[int]) -> int:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if not school_id:
            raise HTTPException(status_code=400, detail="school_id requis pour le Super Admin.")
        return school_id
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Contexte d'établissement requis.")
    return current_user.school_id


@router.post("/fee-reminders/run", response_model=schemas.FeeReminderRunResult)
def run_fee_reminders(
    level2_days: int = Query(15, ge=1, le=365),
    level3_days: int = Query(30, ge=2, le=365),
    cooldown_days: int = Query(3, ge=1, le=90),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Scan outstanding fees and send escalating reminders (see
    services/fee_reminders). Safe to re-run: cooldown + level tracking prevent
    duplicate messages."""
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    if level3_days <= level2_days:
        raise HTTPException(status_code=422, detail="level3_days doit être supérieur à level2_days.")
    summary = fee_reminders.run_fee_reminders(
        db, resolved, current_user,
        level2_days=level2_days, level3_days=level3_days, cooldown_days=cooldown_days,
    )
    audit.record_audit(db, action="automation.fee_reminders.run", current_user=current_user, entity_type="school", entity_id=resolved, details=summary)
    db.commit()
    return summary


@router.get("/fee-reminders/history", response_model=List[schemas.FeeReminderResponse])
def fee_reminder_history(
    limit: int = Query(50, ge=1, le=200),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    rows = (
        db.query(models.FeeReminder, models.Fee, models.User)
        .join(models.Fee, models.Fee.id == models.FeeReminder.fee_id)
        .outerjoin(models.StudentProfile, models.StudentProfile.id == models.FeeReminder.student_id)
        .outerjoin(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(models.FeeReminder.school_id == resolved)
        .order_by(models.FeeReminder.id.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.FeeReminderResponse(
            id=reminder.id, fee_id=fee.id, fee_title=fee.title, student_name=user.full_name if user else None,
            level=reminder.level, outstanding_amount=reminder.outstanding_amount,
            channels=reminder.channels or [], created_at=reminder.created_at,
        )
        for reminder, fee, user in rows
    ]


@router.post("/parent-digest/run", response_model=schemas.ParentDigestRunResult)
def run_parent_digest(
    days: int = Query(7, ge=1, le=31),
    grade_alert_threshold: float = Query(10.0, ge=0, le=20),
    absence_alert_count: int = Query(3, ge=1, le=31),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Compile the weekly digest (grades, absences, payments due) for every
    linked parent, in the parent's language, plus threshold alerts (average
    below the bar, too many absences). Idempotent per window — safe to cron."""
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    summary = parent_digest.run_parent_digest(
        db, resolved, current_user,
        days=days, grade_alert_threshold=grade_alert_threshold, absence_alert_count=absence_alert_count,
    )
    audit.record_audit(db, action="automation.parent_digest.run", current_user=current_user, entity_type="school", entity_id=resolved, details=summary)
    db.commit()
    return summary


@router.get("/parent-digest/history", response_model=List[schemas.ParentDigestNotificationResponse])
def parent_digest_history(
    limit: int = Query(50, ge=1, le=200),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    rows = (
        db.query(models.NotificationHistory)
        .filter(
            models.NotificationHistory.school_id == resolved,
            models.NotificationHistory.event_type.in_(["parent.digest", "parent.alert.average", "parent.alert.absences"]),
        )
        .order_by(models.NotificationHistory.id.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.ParentDigestNotificationResponse(
            id=row.id, event_type=row.event_type, recipient_name=row.recipient_name,
            subject=row.subject, message=row.message, created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/absence-followup/run", response_model=schemas.AbsenceFollowupRunResult)
def run_absence_followup(
    days: int = Query(2, ge=1, le=31),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Send the parent message for every recent unfollowed absence (notification
    in the parent's language + SMS when a parent phone is on file). Each
    Attendance row is followed up at most once — safe to re-run after class or
    daily via cron."""
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    summary = absence_followup.run_absence_followup(db, resolved, current_user, days=days)
    audit.record_audit(db, action="automation.absence_followup.run", current_user=current_user, entity_type="school", entity_id=resolved, details=summary)
    db.commit()
    return summary


@router.post("/anomaly-digest/run", response_model=schemas.AnomalyDigestRunResult)
def run_anomaly_digest(
    days: int = Query(7, ge=1, le=31),
    unpaid_threshold: float = Query(0.3, ge=0, le=1),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Compute the window's operational anomalies (absence spike, unpaid ratio,
    class-size imbalance) and record the brief to the administrator. One digest
    per window per school — safe to cron weekly."""
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    summary = anomaly_digest.run_anomaly_digest(db, resolved, current_user, days=days, unpaid_threshold=unpaid_threshold)
    audit.record_audit(db, action="automation.anomaly_digest.run", current_user=current_user, entity_type="school", entity_id=resolved, details=summary)
    db.commit()
    return summary


@router.get("/rentree/preview", response_model=schemas.RentreePreview)
def rentree_preview(
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Dry-run of the year rollover: per-level promotions, leavers, unmapped
    students and fee schedules to clone. Never writes."""
    _ensure_rentree_admin(current_user)
    resolved = _school_id(current_user, school_id)
    return rentree.plan_rentree(db, resolved)


@router.post("/rentree/run", response_model=schemas.RentreeRunResult)
def rentree_run(
    payload: schemas.RentreeRunRequest,
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Execute the rollover: new current academic year, level→level promotions
    (least-filled class of the next level), leavers archived, fee schedules
    cloned. Refuses (409) if the year name already exists."""
    _ensure_rentree_admin(current_user)
    resolved = _school_id(current_user, school_id)
    summary = rentree.run_rentree(
        db, resolved, current_user,
        new_year_name=payload.new_year_name.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.commit()
    return summary


def _student_or_linked_child(db: Session, current_user: models.User, student_id: Optional[int]) -> models.StudentProfile:
    """Students resolve to themselves; parents to a linked child via student_id."""
    if current_user.role in (models.UserRole.STUDENT, models.UserRole.PUPIL):
        profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil élève introuvable.")
        return profile
    if current_user.role == models.UserRole.PARENT:
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id requis pour un parent.")
        link = db.query(models.ParentStudentLink).filter(
            models.ParentStudentLink.parent_user_id == current_user.id,
            models.ParentStudentLink.student_id == student_id,
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Cet élève n'est pas rattaché à votre compte.")
        profile = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil élève introuvable.")
        return profile
    raise HTTPException(status_code=403, detail="Réservé aux élèves et aux parents.")


@router.get("/study-plan")
def study_plan(
    student_id: Optional[int] = None,
    horizon_days: int = Query(21, ge=7, le=60),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Revision plan built from the student's real timetable, upcoming
    assessments and pending homework. Students see their own plan; parents can
    request a linked child's via student_id."""
    profile = _student_or_linked_child(db, current_user, student_id)
    return student_planner.build_study_plan(db, profile, horizon_days=horizon_days)


@router.get("/explain-grade/grades")
def explain_grade_grades(
    student_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """The student's recent grades with class stats, to pick one to explain."""
    profile = _student_or_linked_child(db, current_user, student_id)
    return grade_explainer.list_grades_with_context(db, profile, limit=limit)


@router.post("/explain-grade/{grade_id}/run")
def explain_grade_run(
    grade_id: int,
    student_id: Optional[int] = None,
    language: str = Query("fr", min_length=2, max_length=5),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """AI walk-through of one of the student's own grades (class context +
    improvement tips). AI-credit-gated on the caller."""
    profile = _student_or_linked_child(db, current_user, student_id)
    result = grade_explainer.explain_grade(db, grade_id, profile, current_user, language=language)
    audit.record_audit(db, action="automation.explain_grade.run", current_user=current_user, entity_type="grade", entity_id=grade_id)
    db.commit()
    return result


@router.post("/homework-reminders/run", response_model=schemas.HomeworkReminderRunResult)
def run_homework_reminders(
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Spaced-repetition homework nudges (D-7 / D-3 / D-1) to students who have
    not submitted. Idempotent per (assignment, student, bucket) — safe to cron
    daily."""
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    summary = student_planner.run_homework_reminders(db, resolved, current_user)
    audit.record_audit(db, action="automation.homework_reminders.run", current_user=current_user, entity_type="school", entity_id=resolved, details=summary)
    db.commit()
    return summary


@router.get("/remediation/assessments")
def remediation_assessments(
    limit: int = Query(30, ge=1, le=100),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Recent assessments with grade stats (average, struggling count) so the
    teacher can pick where remediation is needed."""
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux enseignants et à l'administration.")
    resolved = _school_id(current_user, school_id)
    return remediation.list_assessments_with_stats(db, resolved, limit=limit)


@router.post("/remediation/{assessment_id}/run")
def remediation_run(
    assessment_id: int,
    threshold_ratio: float = Query(0.5, gt=0, le=1),
    language: str = Query("fr", min_length=2, max_length=5),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Generate a personalized AI practice set for every student below the
    threshold on this assessment, delivered as a notification. Idempotent per
    (assessment, student) — re-running only serves newly graded students."""
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux enseignants et à l'administration.")
    resolved = _school_id(current_user, school_id)
    summary = remediation.run_remediation(db, assessment_id, resolved, current_user, threshold_ratio=threshold_ratio, language=language)
    audit.record_audit(db, action="automation.remediation.run", current_user=current_user, entity_type="assessment", entity_id=assessment_id, details={"generated": len(summary["generated"]), "skipped_done": summary["skipped_done"]})
    db.commit()
    return summary


@router.get("/sequence/options")
def sequence_options(
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """(class, subject) pairs with real timetable slots + the current year's
    terms, to parameterize the séquence builder."""
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux enseignants et à l'administration.")
    resolved = _school_id(current_user, school_id)
    return sequence_builder.list_sequence_options(db, resolved)


@router.post("/sequence/run")
def sequence_run(
    class_id: int = Query(..., ge=1),
    subject_id: int = Query(..., ge=1),
    term_id: int = Query(..., ge=1),
    topic: str = Query("", max_length=200),
    language: str = Query("fr", min_length=2, max_length=5),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Generate the term's lesson sequence from the pair's real weekly slots
    (AI-credit-gated); also recorded as a notification to the teacher."""
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux enseignants et à l'administration.")
    resolved = _school_id(current_user, school_id)
    result = sequence_builder.build_sequence(
        db, resolved, current_user,
        class_id=class_id, subject_id=subject_id, term_id=term_id, topic=topic.strip(), language=language,
    )
    audit.record_audit(db, action="automation.sequence.run", current_user=current_user, entity_type="class", entity_id=class_id, details={"subject_id": subject_id, "term_id": term_id})
    db.commit()
    return result


@router.post("/grade-ocr/{assessment_id}/scan")
async def grade_ocr_scan(
    assessment_id: int,
    photo: UploadFile = File(...),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Grade-entry autopilot: photograph a marked list → a vision provider
    (OpenAI/Anthropic) transcribes (name, score) pairs, fuzzy-matched onto the
    assessment's real roster. Returns PROPOSALS for confirmation — nothing is
    saved here. 503 when no vision provider is configured (never faked)."""
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux enseignants et à l'administration.")
    resolved = _school_id(current_user, school_id)
    image_bytes = await photo.read()
    result = grade_ocr.scan_grade_sheet(
        db, assessment_id, resolved, current_user,
        image_bytes=image_bytes, mime_type=photo.content_type or "",
    )
    audit.record_audit(db, action="automation.grade_ocr.scanned", current_user=current_user, entity_type="assessment", entity_id=assessment_id, details={"proposals": len(result["proposals"]), "unmatched": len(result["unmatched"])})
    db.commit()
    return result


@router.post("/grade-ocr/{assessment_id}/confirm", response_model=schemas.GradeOcrConfirmResult)
def grade_ocr_confirm(
    assessment_id: int,
    payload: schemas.GradeOcrConfirmRequest,
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Teacher-confirmed save of the scanned scores (upsert per student,
    range-checked against the assessment's max score)."""
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux enseignants et à l'administration.")
    resolved = _school_id(current_user, school_id)
    summary = grade_ocr.confirm_grades(db, assessment_id, resolved, current_user, entries=payload.entries)
    audit.record_audit(db, action="automation.grade_ocr.confirmed", current_user=current_user, entity_type="assessment", entity_id=assessment_id, details=summary)
    db.commit()
    return summary


@router.post("/absence/{attendance_id}/justify")
def justify_absence(
    attendance_id: int,
    reason: str = Query("", max_length=300),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """One-tap parent action: justify a child's absence straight from the
    notification. The linked parent flips the attendance to EXCUSED with a
    traceable remark; the staff member who recorded the absence is notified."""
    if current_user.role != models.UserRole.PARENT:
        raise HTTPException(status_code=403, detail="Réservé aux parents.")
    attendance = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Absence introuvable.")
    link = db.query(models.ParentStudentLink).filter(
        models.ParentStudentLink.parent_user_id == current_user.id,
        models.ParentStudentLink.student_id == attendance.student_id,
        models.ParentStudentLink.is_active == True,  # noqa: E712
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Cet élève n'est pas rattaché à votre compte.")
    if attendance.status not in (models.AttendanceStatus.ABSENT, models.AttendanceStatus.LATE):
        raise HTTPException(status_code=409, detail="Cette présence n'est pas une absence à justifier.")

    stamp = datetime.utcnow().strftime("%d/%m/%Y")
    note = f"Justifiée par le parent le {stamp}" + (f" — {reason.strip()}" if reason.strip() else "")
    attendance.status = models.AttendanceStatus.EXCUSED
    attendance.remarks = f"{attendance.remarks} | {note}" if attendance.remarks else note

    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == attendance.student_id).first()
    student_name = student.user.full_name if student and student.user else f"#{attendance.student_id}"
    recorder = db.query(models.User).filter(models.User.id == attendance.recorded_by_id).first() if attendance.recorded_by_id else None
    school_id = current_user.school_id or (student.user.school_id if student and student.user else None)
    if school_id:
        automation.record_notification(
            db,
            event_type="absence.justified",
            subject=f"Absence justifiée — {student_name}",
            message=f"L'absence de {student_name} du {attendance.date.strftime('%d/%m/%Y')} a été justifiée par {current_user.full_name}." + (f" Motif : {reason.strip()}" if reason.strip() else ""),
            school_id=school_id,
            student_id=attendance.student_id,
            recipient_user=recorder,
            source_type="attendance",
            source_id=attendance.id,
            current_user=current_user,
        )
    audit.record_audit(db, action="automation.absence.justified", current_user=current_user, entity_type="attendance", entity_id=attendance.id, details={"reason": reason.strip() or None})
    db.commit()
    return {"status": "excused", "attendance_id": attendance.id}


@router.get("/notifications/history", response_model=List[schemas.ParentDigestNotificationResponse])
def automation_notification_history(
    event_type: str = Query(..., min_length=3, max_length=64),
    limit: int = Query(50, ge=1, le=200),
    school_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    """Generic history for automation-recorded notifications (absence.followup,
    anomaly.digest, …) so each Automations card can show what was sent."""
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    rows = (
        db.query(models.NotificationHistory)
        .filter(
            models.NotificationHistory.school_id == resolved,
            models.NotificationHistory.event_type == event_type,
        )
        .order_by(models.NotificationHistory.id.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.ParentDigestNotificationResponse(
            id=row.id, event_type=row.event_type, recipient_name=row.recipient_name,
            subject=row.subject, message=row.message, created_at=row.created_at,
        )
        for row in rows
    ]
