"""Auto-remédiation (automation D, teachers group).

After an assessment, generates a personalized practice set for each student
who scored below the threshold, using the platform AI service (provider-backed
when keys are configured, local fallback otherwise). The practice set is
delivered to the student as a notification (`remediation.assigned`), so it
lands in their existing notification flow and stays reviewable.

Idempotent per (assessment, student): a student who already received a
remediation for this assessment is skipped — re-running after new grades are
entered only serves the newcomers.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..services.ai_service import ai_service
from . import ai_credits, automation


def list_assessments_with_stats(db: Session, school_id: int, *, limit: int = 30) -> list:
    """Recent assessments of the school with grade stats, newest first."""
    rows = (
        db.query(models.Assessment, models.Subject, models.Class)
        .join(models.Subject, models.Subject.id == models.Assessment.subject_id)
        .join(models.Class, models.Class.id == models.Assessment.class_id)
        .filter(models.Class.school_id == school_id)
        .order_by(models.Assessment.date.desc())
        .limit(limit)
        .all()
    )
    result = []
    for assessment, subject, cls in rows:
        grades = db.query(models.Grade).filter(models.Grade.assessment_id == assessment.id).all()
        max_score = assessment.max_score or 20
        below = sum(1 for g in grades if g.score < 0.5 * max_score)
        avg = round(sum(g.score for g in grades) / len(grades), 2) if grades else None
        result.append({
            "id": assessment.id, "title": assessment.title, "subject": subject.name,
            "class_name": cls.name, "date": assessment.date, "max_score": max_score,
            "grades": len(grades), "average": avg, "struggling": below,
        })
    return result


def run_remediation(
    db: Session,
    assessment_id: int,
    school_id: int,
    current_user: models.User,
    *,
    threshold_ratio: float = 0.5,
    language: str = "fr",
) -> dict:
    """Generate + deliver one practice set per struggling student. Returns them."""
    row = (
        db.query(models.Assessment, models.Subject, models.Class)
        .join(models.Subject, models.Subject.id == models.Assessment.subject_id)
        .join(models.Class, models.Class.id == models.Assessment.class_id)
        .filter(models.Assessment.id == assessment_id, models.Class.school_id == school_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Évaluation introuvable dans votre établissement.")
    assessment, subject, cls = row
    max_score = assessment.max_score or 20
    cutoff = threshold_ratio * max_score

    grades = (
        db.query(models.Grade, models.StudentProfile, models.User)
        .join(models.StudentProfile, models.StudentProfile.id == models.Grade.student_id)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(models.Grade.assessment_id == assessment.id)
        .all()
    )

    generated, skipped_done, above = [], 0, 0
    for grade, profile, user in grades:
        if grade.score >= cutoff:
            above += 1
            continue
        already = (
            db.query(models.NotificationHistory)
            .filter(
                models.NotificationHistory.event_type == "remediation.assigned",
                models.NotificationHistory.student_id == profile.id,
                models.NotificationHistory.source_type == "assessment",
                models.NotificationHistory.source_id == assessment.id,
            )
            .first()
        )
        if already:
            skipped_done += 1
            continue

        prompt = (
            f"Create a short personalized practice set in {language} for a student who scored "
            f"{grade.score}/{max_score} on the assessment '{assessment.title}' in subject "
            f"'{subject.name}' (class {cls.name}). "
            f"{f'Teacher comment on the copy: {grade.comment}. ' if grade.comment else ''}"
            "Target the likely weak points at this score level: 3 to 5 exercises of increasing "
            "difficulty with brief hints, then the answers at the end. Encourage the student."
        )
        ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt))
        result = ai_service.generate_response_from_config(prompt, {"module": "automation_remediation"}, db)
        content = result.get("data") or result.get("message") or ""
        ai_credits.record_usage(db, current_user, prompt, content, "automation_remediation", "remediation")

        automation.record_notification(
            db,
            event_type="remediation.assigned",
            subject=f"Exercices de remédiation — {assessment.title}",
            message=content,
            school_id=school_id,
            student_id=profile.id,
            recipient_user=user,
            source_type="assessment",
            source_id=assessment.id,
            current_user=current_user,
        )
        generated.append({
            "student_id": profile.id,
            "student_name": user.full_name,
            "score": grade.score,
            "practice_set": content,
        })

    return {
        "assessment_id": assessment.id,
        "assessment_title": assessment.title,
        "graded": len(grades),
        "generated": generated,
        "skipped_done": skipped_done,
        "above_threshold": above,
    }
