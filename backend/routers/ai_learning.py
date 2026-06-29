"""AI Learning Platform — dedicated content generators (Slice 8, Loop 4 gap).

Lesson / quiz / exam / homework generators built on the existing `ai_service`
(pluggable providers; local fallback when none configured). Each call is
audit-logged. The conversational tutor already exists via the chat + 41-agent
system; this adds structured generator endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import audit, database, models, security
from ..services.ai_service import ai_service

router = APIRouter(prefix="/ai-learning", tags=["AI Learning"])

EDUCATOR_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.TEACHER,
    models.UserRole.TRAINER,
    models.UserRole.INSTRUCTOR,
    models.UserRole.PEDAGOGY_COORDINATOR,
}


class LessonRequest(BaseModel):
    subject: str
    level: str
    topic: str
    language: str = "fr"


class QuizRequest(BaseModel):
    subject: str
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"
    language: str = "fr"


class ExamRequest(BaseModel):
    subject: str
    level: str
    topics: str
    duration_minutes: int = 60
    language: str = "fr"


def _ensure_educator(current_user: models.User) -> None:
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


def _generate(db: Session, current_user: models.User, kind: str, prompt: str) -> dict:
    result = ai_service.generate_response_from_config(prompt, {"module": f"ai_learning_{kind}"}, db)
    audit.record_audit(
        db,
        action=f"ai_learning.{kind}_generated",
        current_user=current_user,
        entity_type="ai_learning",
        entity_id=str(current_user.id),
        details={"kind": kind, "model": result.get("model_name")},
    )
    db.commit()
    return {"kind": kind, "content": result.get("data") or result.get("message"), "model": result.get("model_name")}


@router.post("/generate/lesson")
def generate_lesson(payload: LessonRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_educator(current_user)
    prompt = (
        f"Create a structured lesson plan in {payload.language} for subject '{payload.subject}', "
        f"level '{payload.level}', topic '{payload.topic}'. Include objectives, prerequisites, a "
        "step-by-step plan, activities, and an assessment. Keep it classroom-ready."
    )
    return _generate(db, current_user, "lesson", prompt)


@router.post("/generate/quiz")
def generate_quiz(payload: QuizRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_educator(current_user)
    prompt = (
        f"Create a {payload.difficulty} quiz in {payload.language} on '{payload.topic}' for subject "
        f"'{payload.subject}' with {payload.num_questions} questions. For each: question, options "
        "(if MCQ), the correct answer and a brief explanation."
    )
    return _generate(db, current_user, "quiz", prompt)


@router.post("/generate/exam")
def generate_exam(payload: ExamRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_educator(current_user)
    prompt = (
        f"Create a {payload.duration_minutes}-minute exam in {payload.language} for subject "
        f"'{payload.subject}', level '{payload.level}', covering: {payload.topics}. Include a mark "
        "scheme and total points. Mix question types appropriately."
    )
    return _generate(db, current_user, "exam", prompt)
