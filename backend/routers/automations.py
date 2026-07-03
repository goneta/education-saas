"""Staff automations hub — endpoints that trigger the platform's automation
runs (unpaid-fee reminders, parent digests, …). No background worker is
required: each run is idempotent (anti-spam tracking) so it can be triggered
manually from the Automations page or by an external cron hitting the endpoint.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security
from ..services import fee_reminders

router = APIRouter(prefix="/automations", tags=["Automations"])

ADMIN_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.ACCOUNTANT, models.UserRole.DIRECTION)


def _ensure_admin(current_user: models.User) -> None:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Réservé à l'administration.")


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
