"""Student automations (automation D, students group): study planner +
homework reminders with spaced-repetition nudges.

- `build_study_plan` reads the student's ACTUAL data — class timetable,
  upcoming assessments, pending homework (published assignments without a
  submission from this student) — and derives a revision schedule: spaced
  slots at D-5 (overview), D-2 (practice) and D-1 (final review) before each
  assessment, longer as the date nears. Pure read, computed on demand.
- `run_homework_reminders` nudges each student who has not submitted yet at
  D-7, D-3 and D-1 before an assignment's due date. Idempotent per
  (assignment, student, bucket): the bucket is encoded in the event type
  (`homework.reminder.d3`…), so re-runs and daily crons never double-send.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from . import automation

REVISION_STEPS = (
    (5, "overview", 30),
    (2, "practice", 45),
    (1, "final_review", 60),
)
REMINDER_BUCKETS = ((1, "d1"), (3, "d3"), (7, "d7"))


def build_study_plan(db: Session, profile: models.StudentProfile, *, horizon_days: int = 21) -> dict:
    """Assessments + pending homework + derived revision slots for one student."""
    now = datetime.utcnow()
    horizon = now + timedelta(days=horizon_days)
    class_id = profile.current_class_id

    assessments = []
    homework = []
    slots = []
    timetable = []

    if class_id:
        rows = (
            db.query(models.Assessment, models.Subject)
            .join(models.Subject, models.Subject.id == models.Assessment.subject_id)
            .filter(models.Assessment.class_id == class_id, models.Assessment.date >= now, models.Assessment.date <= horizon)
            .order_by(models.Assessment.date.asc())
            .all()
        )
        assessments = [
            {"id": a.id, "title": a.title, "subject": s.name, "date": a.date, "type": a.type.value if a.type else None, "max_score": a.max_score}
            for a, s in rows
        ]

        submitted_ids = {
            submission.assignment_id
            for submission in db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.student_id == profile.id).all()
        }
        pending = (
            db.query(models.Assignment)
            .filter(
                models.Assignment.class_id == class_id,
                models.Assignment.status == models.AssignmentStatus.PUBLISHED,
                models.Assignment.due_date.isnot(None),
                models.Assignment.due_date >= now,
            )
            .order_by(models.Assignment.due_date.asc())
            .all()
        )
        homework = [
            {"id": h.id, "title": h.title, "subject": h.subject.name if h.subject else None, "due_date": h.due_date}
            for h in pending if h.id not in submitted_ids
        ]

        for a, s in rows:
            for days_before, step, minutes in REVISION_STEPS:
                slot_date = a.date - timedelta(days=days_before)
                if slot_date >= now - timedelta(days=1):
                    slots.append({
                        "date": slot_date,
                        "subject": s.name,
                        "assessment_title": a.title,
                        "assessment_date": a.date,
                        "step": step,
                        "duration_minutes": minutes,
                    })
        slots.sort(key=lambda slot: slot["date"])

        timetable = [
            {"day_of_week": entry.day_of_week.value if entry.day_of_week else None,
             "start_time": entry.start_time.isoformat() if entry.start_time else None,
             "end_time": entry.end_time.isoformat() if entry.end_time else None,
             "subject": entry.subject.name if entry.subject else None}
            for entry in db.query(models.Timetable).filter(models.Timetable.class_id == class_id).all()
        ]

    return {"assessments": assessments, "homework": homework, "revision_slots": slots, "timetable": timetable}


def run_homework_reminders(db: Session, school_id: int, current_user: models.User, *, limit: int = 1000) -> dict:
    """Spaced nudges (D-7 / D-3 / D-1) to students who have not submitted."""
    now = datetime.utcnow()
    summary = {"assignments": 0, "reminders": 0, "skipped_sent": 0, "skipped_submitted": 0}

    assignments = (
        db.query(models.Assignment)
        .filter(
            models.Assignment.school_id == school_id,
            models.Assignment.status == models.AssignmentStatus.PUBLISHED,
            models.Assignment.due_date.isnot(None),
            models.Assignment.due_date >= now,
        )
        .limit(limit)
        .all()
    )

    for assignment in assignments:
        days_left = (assignment.due_date - now).total_seconds() / 86400
        bucket = next((name for threshold, name in REMINDER_BUCKETS if days_left <= threshold), None)
        if not bucket:
            continue
        summary["assignments"] += 1
        event_type = f"homework.reminder.{bucket}"

        submitted_ids = {
            submission.student_id
            for submission in db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.assignment_id == assignment.id).all()
        }
        students = (
            db.query(models.StudentProfile, models.User)
            .join(models.User, models.User.id == models.StudentProfile.user_id)
            .filter(models.StudentProfile.current_class_id == assignment.class_id, models.User.is_active == True)  # noqa: E712
            .all()
        )
        for profile, user in students:
            if profile.id in submitted_ids:
                summary["skipped_submitted"] += 1
                continue
            already = (
                db.query(models.NotificationHistory)
                .filter(
                    models.NotificationHistory.event_type == event_type,
                    models.NotificationHistory.recipient_user_id == user.id,
                    models.NotificationHistory.source_type == "assignment",
                    models.NotificationHistory.source_id == assignment.id,
                )
                .first()
            )
            if already:
                summary["skipped_sent"] += 1
                continue
            subject_name = assignment.subject.name if assignment.subject else ""
            automation.record_notification(
                db,
                event_type=event_type,
                subject=f"Devoir à rendre : {assignment.title}",
                message=f"Rappel : le devoir « {assignment.title} »{f' ({subject_name})' if subject_name else ''} est à rendre le {assignment.due_date.strftime('%d/%m/%Y')}.",
                school_id=school_id,
                student_id=profile.id,
                recipient_user=user,
                source_type="assignment",
                source_id=assignment.id,
                current_user=current_user,
            )
            summary["reminders"] += 1

    return summary
