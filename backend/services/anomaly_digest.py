"""Weekly anomaly digest for school staff (automation D, staff group).

Computes deterministic operational anomalies over a window and records one
brief to the triggering administrator:

- **Absence spike**: absences this window vs the previous window of the same
  length (flagged when current >= spike_factor x previous and above a floor).
- **Unpaid ratio**: outstanding amount / total billed across all fees
  (flagged above unpaid_threshold).
- **Class-size imbalance**: min/max headcount across classes with students
  (flagged when max >= 2 x min).

No AI provider is required — the metrics are computed from the database, so
the digest works in every deployment; wording is plain text. Idempotent per
window: if an `anomaly.digest` for the school exists within the window, the
run is skipped. Safe to cron weekly.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from . import automation

OUTSTANDING_STATUSES = (models.FeeStatus.PENDING, models.FeeStatus.PARTIAL, models.FeeStatus.OVERDUE)
ABSENCE_STATUSES = (models.AttendanceStatus.ABSENT, models.AttendanceStatus.LATE)


def _absence_count(db: Session, school_id: int, start: datetime, end: datetime) -> int:
    return (
        db.query(models.Attendance)
        .join(models.StudentProfile, models.StudentProfile.id == models.Attendance.student_id)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(
            models.User.school_id == school_id,
            models.Attendance.date >= start,
            models.Attendance.date < end,
            models.Attendance.status.in_(ABSENCE_STATUSES),
        )
        .count()
    )


def _outstanding(fee: models.Fee) -> float:
    paid = sum(p.amount for p in (fee.payments or []) if (p.status or "successful") == "successful")
    return max((fee.amount or 0) - paid, 0)


def run_anomaly_digest(
    db: Session,
    school_id: int,
    current_user: models.User,
    *,
    days: int = 7,
    spike_factor: float = 1.5,
    spike_floor: int = 5,
    unpaid_threshold: float = 0.3,
) -> dict:
    """Compute the window's anomalies and notify the triggering admin once per window."""
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    previous_since = since - timedelta(days=days)

    existing = (
        db.query(models.NotificationHistory)
        .filter(
            models.NotificationHistory.event_type == "anomaly.digest",
            models.NotificationHistory.school_id == school_id,
            models.NotificationHistory.created_at >= since,
        )
        .first()
    )
    if existing:
        return {"skipped_cooldown": True, "anomalies": 0, "notified": 0}

    # 1. Absence spike
    current_absences = _absence_count(db, school_id, since, now + timedelta(days=1))
    previous_absences = _absence_count(db, school_id, previous_since, since)
    absence_spike = current_absences >= spike_floor and current_absences >= spike_factor * max(previous_absences, 1)

    # 2. Unpaid ratio
    fees = db.query(models.Fee).filter(models.Fee.school_id == school_id).all()
    total_billed = sum(fee.amount or 0 for fee in fees)
    total_outstanding = sum(_outstanding(fee) for fee in fees if fee.status in OUTSTANDING_STATUSES)
    unpaid_ratio = round(total_outstanding / total_billed, 3) if total_billed else 0.0
    unpaid_flag = unpaid_ratio > unpaid_threshold

    # 3. Class-size imbalance (classes that actually have students)
    counts = {}
    profiles = (
        db.query(models.StudentProfile)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(models.User.school_id == school_id, models.StudentProfile.current_class_id.isnot(None))
        .all()
    )
    for profile in profiles:
        counts[profile.current_class_id] = counts.get(profile.current_class_id, 0) + 1
    size_min = min(counts.values()) if counts else 0
    size_max = max(counts.values()) if counts else 0
    imbalance_flag = len(counts) >= 2 and size_min > 0 and size_max >= 2 * size_min

    anomalies = sum(1 for flag in (absence_spike, unpaid_flag, imbalance_flag) if flag)

    lines = [f"Brief anomalies — {days} derniers jours :"]
    if absence_spike:
        lines.append(f"⚠ Pic d'absences : {current_absences} absences/retards contre {previous_absences} la période précédente.")
    else:
        lines.append(f"Absences/retards : {current_absences} (période précédente : {previous_absences}) — normal.")
    if unpaid_flag:
        lines.append(f"⚠ Impayés : {unpaid_ratio * 100:.0f}% du facturé reste dû ({total_outstanding:,.0f} sur {total_billed:,.0f}).")
    else:
        lines.append(f"Impayés : {unpaid_ratio * 100:.0f}% du facturé — sous le seuil de {unpaid_threshold * 100:.0f}%.")
    if imbalance_flag:
        lines.append(f"⚠ Déséquilibre des classes : de {size_min} à {size_max} élèves par classe.")
    elif counts:
        lines.append(f"Effectifs par classe : de {size_min} à {size_max} élèves — équilibré.")
    else:
        lines.append("Effectifs par classe : aucune classe avec élèves affectés.")
    lines.append("Actions suggérées : relancer les impayés (Automatisations), vérifier l'assiduité des classes concernées, rééquilibrer les affectations si besoin." if anomalies else "Aucune anomalie détectée sur la période.")

    automation.record_notification(
        db,
        event_type="anomaly.digest",
        subject=f"Brief anomalies ({anomalies} signal(s))",
        message="\n".join(lines),
        school_id=school_id,
        recipient_user=current_user,
        source_type="automation",
        current_user=current_user,
    )

    return {
        "skipped_cooldown": False,
        "anomalies": anomalies,
        "notified": 1,
        "absences_current": current_absences,
        "absences_previous": previous_absences,
        "absence_spike": absence_spike,
        "unpaid_ratio": unpaid_ratio,
        "unpaid_flag": unpaid_flag,
        "class_size_min": size_min,
        "class_size_max": size_max,
        "imbalance_flag": imbalance_flag,
    }
