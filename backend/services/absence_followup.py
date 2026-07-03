"""Absence follow-up automation (automation D, teachers group).

Auto-drafts and sends the parent message when a student is marked absent:
scans recent unexcused absences, and for each one not yet followed up sends a
notification to the linked parent account (in the parent's language) and
queues an SMS when a parent phone is on file. Idempotent: each Attendance row
is followed up at most once (NotificationHistory source tracking), so the
runner can be triggered after class, daily, or by cron.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from . import automation

SUPPORTED_LANGS = ("fr", "en", "es", "sw")

TEMPLATES = {
    "fr": {
        "subject": "Absence de {student}",
        "message": "Bonjour, nous vous informons que {student} a été noté(e) absent(e) le {date}{subject_part}. Si cette absence est justifiée, merci de transmettre le justificatif à l'établissement.",
        "subject_part": " au cours de {subject}",
    },
    "en": {
        "subject": "Absence of {student}",
        "message": "Hello, please note that {student} was marked absent on {date}{subject_part}. If this absence is justified, please send the supporting document to the school.",
        "subject_part": " during the {subject} class",
    },
    "es": {
        "subject": "Ausencia de {student}",
        "message": "Buenos días, le informamos de que {student} fue marcado/a ausente el {date}{subject_part}. Si la ausencia está justificada, envíe el justificante al centro.",
        "subject_part": " en la clase de {subject}",
    },
    "sw": {
        "subject": "Kutokuwepo kwa {student}",
        "message": "Habari, tunakujulisha kuwa {student} aliwekwa alama ya kutokuwepo tarehe {date}{subject_part}. Ikiwa kutokuwepo huku kuna sababu halali, tafadhali wasilisha uthibitisho shuleni.",
        "subject_part": " katika kipindi cha {subject}",
    },
}


def _parent_lang(db: Session, parent: models.User) -> str:
    pref = db.query(models.UserPreference).filter(models.UserPreference.user_id == parent.id).first()
    lang = (pref.language or "").lower()[:2] if pref and pref.language else ""
    return lang if lang in SUPPORTED_LANGS else "fr"


def run_absence_followup(db: Session, school_id: int, current_user: models.User, *, days: int = 2, limit: int = 500) -> dict:
    """Follow up each recent ABSENT record exactly once. Returns a summary."""
    since = datetime.utcnow() - timedelta(days=days)
    summary = {"scanned": 0, "notified": 0, "sms_queued": 0, "skipped_done": 0, "skipped_no_contact": 0}

    rows = (
        db.query(models.Attendance, models.StudentProfile, models.User)
        .join(models.StudentProfile, models.StudentProfile.id == models.Attendance.student_id)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(
            models.User.school_id == school_id,
            models.Attendance.date >= since,
            models.Attendance.status == models.AttendanceStatus.ABSENT,
        )
        .order_by(models.Attendance.id.asc())
        .limit(limit)
        .all()
    )

    for attendance, profile, student_user in rows:
        summary["scanned"] += 1

        done = (
            db.query(models.NotificationHistory)
            .filter(
                models.NotificationHistory.event_type == "absence.followup",
                models.NotificationHistory.source_type == "attendance",
                models.NotificationHistory.source_id == attendance.id,
            )
            .first()
        )
        if done:
            summary["skipped_done"] += 1
            continue

        link = (
            db.query(models.ParentStudentLink)
            .filter(
                models.ParentStudentLink.student_id == profile.id,
                models.ParentStudentLink.is_active == True,  # noqa: E712
            )
            .first()
        )
        parent = link.parent if link else None
        parent_phone = profile.parent_phone_e164 or profile.parent_phone
        if not parent and not parent_phone:
            summary["skipped_no_contact"] += 1
            continue

        subject_name = None
        if attendance.timetable_id:
            timetable = db.query(models.Timetable).filter(models.Timetable.id == attendance.timetable_id).first()
            if timetable and timetable.subject:
                subject_name = timetable.subject.name

        t = TEMPLATES[_parent_lang(db, parent) if parent else "fr"]
        student_name = student_user.full_name or f"#{profile.id}"
        subject_part = t["subject_part"].format(subject=subject_name) if subject_name else ""
        message = t["message"].format(student=student_name, date=attendance.date.strftime("%d/%m/%Y"), subject_part=subject_part)

        automation.record_notification(
            db,
            event_type="absence.followup",
            subject=t["subject"].format(student=student_name),
            message=message,
            school_id=school_id,
            student_id=profile.id,
            recipient_user=parent,
            recipient_contact=None if parent else parent_phone,
            source_type="attendance",
            source_id=attendance.id,
            current_user=current_user,
        )
        summary["notified"] += 1

        if parent_phone:
            db.add(models.SmsMessage(
                recipient_phone=parent_phone,
                recipient_name=profile.parent_name,
                event_type="absence_followup",
                message=message,
                status="queued",
                student_id=profile.id,
                school_id=school_id,
                created_by_id=current_user.id if current_user else None,
            ))
            summary["sms_queued"] += 1

    return summary
