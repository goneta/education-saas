"""Auto-relance des impayés — the unpaid-fee reminder automation.

Scans a school's fees that are pending/partial/overdue and past their due date,
computes the true outstanding amount (amount − successful payments), and sends
escalating reminders:

- level 1 (due < `level2_days` ago): gentle reminder to the student account
  (in-app notification) + SMS queued to the parent phone when available;
- level 2 (≥ `level2_days`): firm reminder, same channels;
- level 3 (≥ `level3_days`): urgent reminder AND an escalation notification to
  the school administrator who triggered the run.

Anti-spam: a fee reminded within `cooldown_days` is skipped, and a fee never
repeats a level it has already received unless the level escalated. Every
reminder actually sent is recorded as a `FeeReminder` row, so the automation is
idempotent when re-run (cron or manual) and fully auditable.

No background worker is required: expose the runner behind an admin endpoint —
call it manually from the Automations page or schedule it externally (cron
hitting the endpoint)."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models
from . import automation


REMINDER_STATUSES = [models.FeeStatus.PENDING, models.FeeStatus.PARTIAL, models.FeeStatus.OVERDUE]


def _outstanding(fee: models.Fee) -> float:
    paid = sum(p.amount for p in (fee.payments or []) if (p.status or "successful") == "successful")
    return round(max(fee.amount - paid, 0), 2)


def _level_for(days_overdue: int, level2_days: int, level3_days: int) -> int:
    if days_overdue >= level3_days:
        return 3
    if days_overdue >= level2_days:
        return 2
    return 1


def _message_for(level: int, fee: models.Fee, outstanding: float, days_overdue: int) -> str:
    base = f"{fee.title} — reste dû {outstanding:,.0f} ({days_overdue} j de retard)".replace(",", " ")
    if level == 1:
        return f"Rappel : {base}. Merci de régulariser le paiement."
    if level == 2:
        return f"Relance : {base}. Merci de régulariser rapidement pour éviter une suspension des services."
    return f"URGENT : {base}. Sans règlement, le dossier sera transmis à l'administration."


def run_fee_reminders(
    db: Session,
    school_id: int,
    current_user: Optional[models.User] = None,
    *,
    level2_days: int = 15,
    level3_days: int = 30,
    cooldown_days: int = 3,
    limit: int = 500,
) -> dict:
    """Scan and remind. Returns a summary; commit is the caller's job."""
    now = datetime.now(timezone.utc)
    fees = (
        db.query(models.Fee)
        .filter(
            models.Fee.school_id == school_id,
            models.Fee.status.in_(REMINDER_STATUSES),
            models.Fee.due_date != None,  # noqa: E711
            models.Fee.student_id != None,  # noqa: E711
        )
        .order_by(models.Fee.due_date.asc())
        .limit(limit)
        .all()
    )

    summary = {"scanned": 0, "reminded": 0, "escalated": 0, "skipped_cooldown": 0, "skipped_not_due": 0, "skipped_paid": 0, "sms_queued": 0}

    for fee in fees:
        summary["scanned"] += 1
        due = fee.due_date if fee.due_date.tzinfo else fee.due_date.replace(tzinfo=timezone.utc)
        days_overdue = (now - due).days
        if days_overdue < 0:
            summary["skipped_not_due"] += 1
            continue
        outstanding = _outstanding(fee)
        if outstanding <= 0:
            summary["skipped_paid"] += 1
            continue

        level = _level_for(days_overdue, level2_days, level3_days)

        last = (
            db.query(models.FeeReminder)
            .filter(models.FeeReminder.fee_id == fee.id)
            .order_by(models.FeeReminder.id.desc())
            .first()
        )
        if last is not None:
            last_at = last.created_at if last.created_at and last.created_at.tzinfo else (last.created_at.replace(tzinfo=timezone.utc) if last.created_at else None)
            in_cooldown = last_at is not None and (now - last_at) < timedelta(days=cooldown_days)
            # Skip when still cooling down, or when this level was already sent.
            if in_cooldown or last.level >= level:
                summary["skipped_cooldown"] += 1
                continue

        message = _message_for(level, fee, outstanding, days_overdue)
        channels = ["notification"]
        student_user = fee.student.user if fee.student else None

        automation.record_notification(
            db,
            event_type="fee.reminder",
            subject="Rappel de paiement" if level < 3 else "Relance urgente de paiement",
            message=message,
            school_id=school_id,
            student_id=fee.student_id,
            recipient_user=student_user,
            source_type="fee",
            source_id=fee.id,
            current_user=current_user,
        )

        parent_phone = fee.student.parent_phone_e164 or fee.student.parent_phone if fee.student else None
        if parent_phone:
            db.add(models.SmsMessage(
                recipient_phone=parent_phone,
                recipient_name=fee.student.parent_name if fee.student else None,
                event_type="payment_late",
                message=message,
                status="queued",
                student_id=fee.student_id,
                school_id=school_id,
                created_by_id=current_user.id if current_user else None,
            ))
            channels.append("sms")
            summary["sms_queued"] += 1

        if level == 3 and current_user is not None:
            automation.record_notification(
                db,
                event_type="fee.reminder.escalated",
                subject="Impayé escaladé",
                message=f"Impayé de niveau 3 : {message}",
                school_id=school_id,
                student_id=fee.student_id,
                recipient_user=current_user,
                source_type="fee",
                source_id=fee.id,
                current_user=current_user,
            )
            summary["escalated"] += 1

        db.add(models.FeeReminder(
            fee_id=fee.id,
            school_id=school_id,
            student_id=fee.student_id,
            level=level,
            outstanding_amount=outstanding,
            channels=channels,
        ))
        summary["reminded"] += 1

    return summary
