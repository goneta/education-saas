"""Staff automations hub — endpoints that trigger the platform's automation
runs (unpaid-fee reminders, parent digests, …). No background worker is
required: each run is idempotent (anti-spam tracking) so it can be triggered
manually from the Automations page or by an external cron hitting the endpoint.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security
from datetime import datetime

from ..services import absence_followup, anomaly_digest, fee_reminders, parent_digest, rentree

router = APIRouter(prefix="/automations", tags=["Automations"])

ADMIN_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.ACCOUNTANT, models.UserRole.DIRECTION)
RENTREE_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION)


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
