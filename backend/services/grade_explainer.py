"""Explain-my-grade (automation D, students group).

On-demand AI walk-through of a grade: the student (or a linked parent) picks
one of their grades and gets a personalized explanation — how the score sits
against the class (average, best), what the teacher's comment means, and 2–3
targeted improvement tips. Generation goes through the platform AI service
(provider-backed or local fallback) and is AI-credit-gated on the caller.

Pure on-demand reads — nothing is persisted beyond the audit/usage records.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..services.ai_service import ai_service
from . import ai_credits


def list_grades_with_context(db: Session, profile: models.StudentProfile, *, limit: int = 20) -> list:
    """The student's recent grades with class stats, newest assessment first."""
    rows = (
        db.query(models.Grade, models.Assessment, models.Subject)
        .join(models.Assessment, models.Assessment.id == models.Grade.assessment_id)
        .join(models.Subject, models.Subject.id == models.Assessment.subject_id)
        .filter(models.Grade.student_id == profile.id)
        .order_by(models.Assessment.date.desc())
        .limit(limit)
        .all()
    )
    result = []
    for grade, assessment, subject in rows:
        class_scores = [g.score for g in db.query(models.Grade).filter(models.Grade.assessment_id == assessment.id).all()]
        result.append({
            "grade_id": grade.id,
            "assessment_title": assessment.title,
            "subject": subject.name,
            "date": assessment.date,
            "score": grade.score,
            "max_score": assessment.max_score or 20,
            "class_average": round(sum(class_scores) / len(class_scores), 2) if class_scores else None,
            "class_best": max(class_scores) if class_scores else None,
            "class_size": len(class_scores),
            "comment": grade.comment,
        })
    return result


def explain_grade(
    db: Session,
    grade_id: int,
    profile: models.StudentProfile,
    current_user: models.User,
    *,
    language: str = "fr",
) -> dict:
    """AI walk-through of one of the student's own grades."""
    row = (
        db.query(models.Grade, models.Assessment, models.Subject)
        .join(models.Assessment, models.Assessment.id == models.Grade.assessment_id)
        .join(models.Subject, models.Subject.id == models.Assessment.subject_id)
        .filter(models.Grade.id == grade_id, models.Grade.student_id == profile.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Note introuvable pour cet élève.")
    grade, assessment, subject = row
    max_score = assessment.max_score or 20

    class_scores = [g.score for g in db.query(models.Grade).filter(models.Grade.assessment_id == assessment.id).all()]
    class_average = round(sum(class_scores) / len(class_scores), 2) if class_scores else None
    class_best = max(class_scores) if class_scores else None
    rank = sorted(class_scores, reverse=True).index(grade.score) + 1 if class_scores else None

    prompt = (
        f"You are a supportive school tutor. Explain in {language}, to the student directly "
        f"(second person), their result on the assessment '{assessment.title}' in subject "
        f"'{subject.name}': they scored {grade.score}/{max_score}; the class average is "
        f"{class_average}/{max_score}, the best score {class_best}/{max_score}, and they rank "
        f"{rank} out of {len(class_scores)}. "
        f"{f'Teacher comment on the copy: {grade.comment}. ' if grade.comment else ''}"
        "Walk them through what this result means, what likely went well and what did not, then "
        "give 2-3 concrete, encouraging improvement tips for the next assessment. Keep it short "
        "and positive — no jargon."
    )
    ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "automation_explain_grade"}, db)
    explanation = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, current_user, prompt, explanation, "automation_explain_grade", "explain_grade")

    return {
        "grade_id": grade.id,
        "assessment_title": assessment.title,
        "subject": subject.name,
        "score": grade.score,
        "max_score": max_score,
        "class_average": class_average,
        "class_best": class_best,
        "rank": rank,
        "class_size": len(class_scores),
        "explanation": explanation,
    }
