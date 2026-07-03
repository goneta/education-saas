"""Weekly parent digest + threshold alerts (automation C).

For every active parent-student link of the school, compiles the child's week
(new grades, absences/lates, outstanding fees) into one digest notification in
the parent's language, and fires threshold alerts (average below the bar,
too many absences). Idempotent: a student whose parent already received a
digest within the window is skipped, so the runner can be re-run or scheduled
via an external cron without spamming families.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from . import automation

OUTSTANDING_STATUSES = (models.FeeStatus.PENDING, models.FeeStatus.PARTIAL, models.FeeStatus.OVERDUE)
ABSENCE_STATUSES = (models.AttendanceStatus.ABSENT, models.AttendanceStatus.LATE)
SUPPORTED_LANGS = ("fr", "en", "es", "sw")

TEMPLATES = {
    "fr": {
        "subject": "Résumé hebdomadaire — {student}",
        "header": "Résumé de la semaine pour {student} :",
        "grades": "{count} nouvelle(s) note(s), moyenne {avg}/20.",
        "no_grades": "Aucune nouvelle note cette semaine.",
        "absences": "{absent} absence(s) et {late} retard(s) sur la période.",
        "no_absences": "Aucune absence ni retard sur la période.",
        "fees": "Reste à payer : {amount} ({count} frais en attente).",
        "no_fees": "Aucun paiement en attente.",
        "avg_alert_subject": "Alerte moyenne — {student}",
        "avg_alert": "La moyenne de {student} sur la période est de {avg}/20, sous le seuil de {threshold}/20.",
        "abs_alert_subject": "Alerte assiduité — {student}",
        "abs_alert": "{student} compte {count} absence(s)/retard(s) sur les {days} derniers jours.",
    },
    "en": {
        "subject": "Weekly digest — {student}",
        "header": "This week's summary for {student}:",
        "grades": "{count} new grade(s), average {avg}/20.",
        "no_grades": "No new grade this week.",
        "absences": "{absent} absence(s) and {late} late arrival(s) over the period.",
        "no_absences": "No absence or late arrival over the period.",
        "fees": "Outstanding balance: {amount} ({count} pending fee(s)).",
        "no_fees": "No pending payment.",
        "avg_alert_subject": "Average alert — {student}",
        "avg_alert": "{student}'s average over the period is {avg}/20, below the {threshold}/20 bar.",
        "abs_alert_subject": "Attendance alert — {student}",
        "abs_alert": "{student} has {count} absence(s)/late(s) over the last {days} days.",
    },
    "es": {
        "subject": "Resumen semanal — {student}",
        "header": "Resumen de la semana para {student}:",
        "grades": "{count} nota(s) nueva(s), media {avg}/20.",
        "no_grades": "Ninguna nota nueva esta semana.",
        "absences": "{absent} ausencia(s) y {late} retraso(s) en el período.",
        "no_absences": "Sin ausencias ni retrasos en el período.",
        "fees": "Saldo pendiente: {amount} ({count} cuota(s) pendiente(s)).",
        "no_fees": "Ningún pago pendiente.",
        "avg_alert_subject": "Alerta de media — {student}",
        "avg_alert": "La media de {student} en el período es {avg}/20, por debajo del umbral de {threshold}/20.",
        "abs_alert_subject": "Alerta de asistencia — {student}",
        "abs_alert": "{student} acumula {count} ausencia(s)/retraso(s) en los últimos {days} días.",
    },
    "sw": {
        "subject": "Muhtasari wa wiki — {student}",
        "header": "Muhtasari wa wiki kwa {student}:",
        "grades": "Alama mpya {count}, wastani {avg}/20.",
        "no_grades": "Hakuna alama mpya wiki hii.",
        "absences": "Kutokuwepo {absent} na kuchelewa {late} katika kipindi.",
        "no_absences": "Hakuna kutokuwepo wala kuchelewa katika kipindi.",
        "fees": "Salio linalodaiwa: {amount} (ada {count} zinasubiri).",
        "no_fees": "Hakuna malipo yanayosubiri.",
        "avg_alert_subject": "Tahadhari ya wastani — {student}",
        "avg_alert": "Wastani wa {student} katika kipindi ni {avg}/20, chini ya kizingiti cha {threshold}/20.",
        "abs_alert_subject": "Tahadhari ya mahudhurio — {student}",
        "abs_alert": "{student} ana kutokuwepo/kuchelewa {count} katika siku {days} zilizopita.",
    },
}


def _parent_lang(db: Session, parent: models.User) -> str:
    pref = db.query(models.UserPreference).filter(models.UserPreference.user_id == parent.id).first()
    lang = (pref.language or "").lower()[:2] if pref and pref.language else ""
    return lang if lang in SUPPORTED_LANGS else "fr"


def _outstanding(fee: models.Fee) -> float:
    paid = sum(p.amount for p in (fee.payments or []) if (p.status or "successful") == "successful")
    return max((fee.amount or 0) - paid, 0)


def run_parent_digest(
    db: Session,
    school_id: int,
    current_user: models.User,
    *,
    days: int = 7,
    grade_alert_threshold: float = 10.0,
    absence_alert_count: int = 3,
    limit: int = 1000,
) -> dict:
    """One digest per (parent, child); threshold alerts ride along. Returns a summary."""
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    summary = {"links": 0, "digests": 0, "grade_alerts": 0, "absence_alerts": 0, "skipped_cooldown": 0}

    links = (
        db.query(models.ParentStudentLink)
        .join(models.StudentProfile, models.StudentProfile.id == models.ParentStudentLink.student_id)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(
            models.ParentStudentLink.is_active == True,  # noqa: E712
            models.User.school_id == school_id,
        )
        .limit(limit)
        .all()
    )

    for link in links:
        summary["links"] += 1
        parent, profile = link.parent, link.student
        if not parent or not profile:
            continue
        student_name = profile.user.full_name if profile.user else f"#{profile.id}"

        # Anti-spam: one digest per window per (parent, child).
        recent = (
            db.query(models.NotificationHistory)
            .filter(
                models.NotificationHistory.event_type == "parent.digest",
                models.NotificationHistory.recipient_user_id == parent.id,
                models.NotificationHistory.student_id == profile.id,
                models.NotificationHistory.created_at >= since,
            )
            .first()
        )
        if recent:
            summary["skipped_cooldown"] += 1
            continue

        grades = (
            db.query(models.Grade, models.Assessment)
            .join(models.Assessment, models.Assessment.id == models.Grade.assessment_id)
            .filter(models.Grade.student_id == profile.id, models.Assessment.date >= since)
            .all()
        )
        normalized = [g.score / (a.max_score or 20) * 20 for g, a in grades if a.max_score]
        avg20 = round(sum(normalized) / len(normalized), 2) if normalized else None

        absences = (
            db.query(models.Attendance)
            .filter(
                models.Attendance.student_id == profile.id,
                models.Attendance.date >= since,
                models.Attendance.status.in_(ABSENCE_STATUSES),
            )
            .all()
        )
        absent_count = sum(1 for a in absences if a.status == models.AttendanceStatus.ABSENT)
        late_count = sum(1 for a in absences if a.status == models.AttendanceStatus.LATE)

        pending_fees = (
            db.query(models.Fee)
            .filter(models.Fee.student_id == profile.id, models.Fee.status.in_(OUTSTANDING_STATUSES))
            .all()
        )
        outstanding_fees = [(fee, _outstanding(fee)) for fee in pending_fees]
        outstanding_fees = [(fee, due) for fee, due in outstanding_fees if due > 0]
        total_due = round(sum(due for _fee, due in outstanding_fees), 2)

        t = TEMPLATES[_parent_lang(db, parent)]
        lines = [t["header"].format(student=student_name)]
        lines.append(t["grades"].format(count=len(grades), avg=avg20) if grades else t["no_grades"])
        lines.append(t["absences"].format(absent=absent_count, late=late_count) if absences else t["no_absences"])
        lines.append(t["fees"].format(amount=f"{total_due:,.0f}", count=len(outstanding_fees)) if outstanding_fees else t["no_fees"])

        automation.record_notification(
            db,
            event_type="parent.digest",
            subject=t["subject"].format(student=student_name),
            message="\n".join(lines),
            school_id=school_id,
            student_id=profile.id,
            recipient_user=parent,
            source_type="automation",
            current_user=current_user,
        )
        summary["digests"] += 1

        if avg20 is not None and avg20 < grade_alert_threshold:
            automation.record_notification(
                db,
                event_type="parent.alert.average",
                subject=t["avg_alert_subject"].format(student=student_name),
                message=t["avg_alert"].format(student=student_name, avg=avg20, threshold=grade_alert_threshold),
                school_id=school_id,
                student_id=profile.id,
                recipient_user=parent,
                source_type="automation",
                current_user=current_user,
            )
            summary["grade_alerts"] += 1

        if len(absences) >= absence_alert_count:
            automation.record_notification(
                db,
                event_type="parent.alert.absences",
                subject=t["abs_alert_subject"].format(student=student_name),
                message=t["abs_alert"].format(student=student_name, count=len(absences), days=days),
                school_id=school_id,
                student_id=profile.id,
                recipient_user=parent,
                source_type="automation",
                current_user=current_user,
            )
            summary["absence_alerts"] += 1

    return summary
