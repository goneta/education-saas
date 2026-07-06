"""Homework / exercise module router.

Teacher endpoints (create manual + AI, publish, grade, AI-grade, roster,
push-to-gradebook, stats) and student/parent endpoints (list, open/submit,
view corrected copy + answer key when released). Everything is school-scoped
and role-gated; AI generations are credit-gated in services/assignments.py.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import audit, database, models, security
from ..services import assignments as svc
from ..services import school_context

router = APIRouter(prefix="/assignments", tags=["Assignments"])

EDUCATOR_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION, models.UserRole.TEACHER)
STUDENT_ROLES = (models.UserRole.STUDENT, models.UserRole.PUPIL)


def _ensure_educator(current_user: models.User) -> None:
    if current_user.role not in EDUCATOR_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux enseignants et à l'administration.")


def _resolved_school(db: Session, current_user: models.User) -> int:
    if current_user.school_id:
        return current_user.school_id
    ctx = school_context.resolve_context(db, current_user)
    return ctx.school_id


def _student_profile(db: Session, current_user: models.User, student_id: Optional[int]) -> models.StudentProfile:
    if current_user.role in STUDENT_ROLES:
        profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil élève introuvable.")
        return profile
    if current_user.role == models.UserRole.PARENT:
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id requis pour un parent.")
        link = db.query(models.ParentStudentLink).filter(
            models.ParentStudentLink.parent_user_id == current_user.id,
            models.ParentStudentLink.student_id == student_id,
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Cet élève n'est pas rattaché à votre compte.")
        profile = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil élève introuvable.")
        return profile
    raise HTTPException(status_code=403, detail="Réservé aux élèves et aux parents.")


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #
class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    instructions: Optional[str] = None
    assignment_type: str = "devoir"
    mode: str = "online"
    class_id: int
    subject_id: Optional[int] = None
    content: Optional[dict] = None
    answer_key: Optional[dict] = None
    max_score: float = 20
    open_at: Optional[str] = None
    due_date: Optional[str] = None
    duration_minutes: Optional[int] = None
    max_attempts: int = 1
    late_penalty: float = 0
    allow_groups: bool = False
    target_student_ids: Optional[List[int]] = None
    answer_key_release: str = "after_due"
    ai_generated: bool = False


class AiGenerateRequest(BaseModel):
    subject: str
    level: str = ""
    chapter: str = ""
    skills: str = ""
    assignment_type: str = "devoir"
    difficulty: str = "moyen"
    num_questions: int = Field(default=8, ge=1, le=40)
    question_types: str = ""
    language: str = "fr"


class GradeRequest(BaseModel):
    score: float
    feedback: Optional[str] = None
    annotations: Optional[list] = None
    publish: bool = True


class SubmitRequest(BaseModel):
    answers: Optional[dict] = None
    content_text: Optional[str] = None
    attachment_urls: Optional[List[str]] = None


class AutosaveRequest(BaseModel):
    answers: dict = Field(default_factory=dict)
    content_text: Optional[str] = None


def _assignment_public(a: models.Assignment, *, include_answer_key: bool = False, include_content: bool = True) -> dict:
    data = {
        "id": a.id, "title": a.title, "instructions": a.instructions,
        "assignment_type": a.assignment_type, "mode": a.mode, "status": a.status.value,
        "class_id": a.class_id, "subject_id": a.subject_id, "max_score": a.max_score,
        "open_at": a.open_at, "due_date": a.due_date, "duration_minutes": a.duration_minutes,
        "max_attempts": a.max_attempts, "late_penalty": a.late_penalty, "allow_groups": a.allow_groups,
        "answer_key_release": a.answer_key_release, "ai_generated": a.ai_generated, "created_at": a.created_at,
    }
    if include_content:
        data["content"] = a.content
    if include_answer_key:
        data["answer_key"] = a.answer_key
    return data


# --------------------------------------------------------------------------- #
# Teacher: creation & lifecycle
# --------------------------------------------------------------------------- #
@router.post("")
def create_assignment(payload: AssignmentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    row = svc.create_assignment(db, current_user, school_id, payload=payload.model_dump())
    audit.record_audit(db, action="assignment.created", current_user=current_user, entity_type="assignment", entity_id=row.id)
    db.commit()
    return _assignment_public(row, include_answer_key=True)


@router.post("/ai-generate")
def ai_generate(payload: AiGenerateRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Generate an assignment's questions + answer key (corrigé) with the AI —
    returned for review; the teacher then POSTs it to /assignments to save."""
    _ensure_educator(current_user)
    result = svc.generate_ai(db, current_user, **payload.model_dump())
    db.commit()
    return result


@router.post("/{assignment_id}/publish")
def publish_assignment(assignment_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    assignment = svc.teacher_assignment_or_404(db, assignment_id, school_id)
    svc.publish(db, assignment, current_user)
    audit.record_audit(db, action="assignment.published", current_user=current_user, entity_type="assignment", entity_id=assignment.id)
    db.commit()
    return _assignment_public(assignment)


@router.get("/teaching")
def list_teaching(status: Optional[str] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Teacher dashboard: the assignments they own, with stage counts."""
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    query = db.query(models.Assignment).filter(models.Assignment.school_id == school_id)
    if current_user.role == models.UserRole.TEACHER:
        query = query.filter(models.Assignment.teacher_id == current_user.id)
    if status:
        query = query.filter(models.Assignment.status == models.AssignmentStatus(status))
    rows = query.order_by(models.Assignment.created_at.desc()).limit(500).all()
    return [{**_assignment_public(r, include_content=False), "stats": svc.stats(db, r)} for r in rows]


@router.get("/{assignment_id}/roster")
def grading_roster(assignment_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """« Donner des notes » : per-student status (submitted / late / absent)."""
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    assignment = svc.teacher_assignment_or_404(db, assignment_id, school_id)
    return {"assignment": _assignment_public(assignment, include_answer_key=True), "roster": svc.submission_roster(db, assignment), "stats": svc.stats(db, assignment)}


# --------------------------------------------------------------------------- #
# Teacher: grading
# --------------------------------------------------------------------------- #
def _teacher_submission_or_404(db: Session, submission_id: int, school_id: int) -> models.AssignmentSubmission:
    sub = (
        db.query(models.AssignmentSubmission)
        .join(models.Assignment, models.Assignment.id == models.AssignmentSubmission.assignment_id)
        .filter(models.AssignmentSubmission.id == submission_id, models.Assignment.school_id == school_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Copie introuvable.")
    return sub


@router.post("/submissions/{submission_id}/grade")
def grade_submission(submission_id: int, payload: GradeRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    sub = _teacher_submission_or_404(db, submission_id, school_id)
    svc.grade(db, sub, current_user, score=payload.score, feedback=payload.feedback, annotations=payload.annotations, publish_grade=payload.publish)
    audit.record_audit(db, action="assignment.graded", current_user=current_user, entity_type="assignment_submission", entity_id=sub.id, details={"score": sub.score, "published": payload.publish})
    db.commit()
    return {"submission_id": sub.id, "score": sub.score, "status": sub.workflow_status}


@router.post("/submissions/{submission_id}/ai-grade")
def ai_grade_submission(submission_id: int, language: str = Query("fr", min_length=2, max_length=5), db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """AI proposes a score + feedback against the corrigé; not final until the
    teacher confirms via /grade."""
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    sub = _teacher_submission_or_404(db, submission_id, school_id)
    result = svc.ai_grade(db, sub, current_user, language=language)
    audit.record_audit(db, action="assignment.ai_graded", current_user=current_user, entity_type="assignment_submission", entity_id=sub.id)
    db.commit()
    return {"submission_id": sub.id, "proposed": result}


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Open a copy for grading (teacher) — full answers, attachments, feedback."""
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    sub = _teacher_submission_or_404(db, submission_id, school_id)
    student = sub.student.user if sub.student else None
    return {
        "id": sub.id, "assignment_id": sub.assignment_id, "student_id": sub.student_id,
        "student_name": student.full_name if student else None,
        "status": sub.workflow_status, "is_late": sub.is_late, "attempt_number": sub.attempt_number,
        "answers": sub.answers, "content_text": sub.content_text, "attachment_urls": sub.attachment_urls,
        "score": sub.score, "feedback": sub.feedback, "annotations": sub.annotations,
        "ai_graded": sub.ai_graded, "ai_feedback": sub.ai_feedback, "submitted_at": sub.submitted_at,
    }


@router.post("/{assignment_id}/push-to-gradebook")
def push_to_gradebook(assignment_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_educator(current_user)
    school_id = _resolved_school(db, current_user)
    assignment = svc.teacher_assignment_or_404(db, assignment_id, school_id)
    result = svc.push_to_gradebook(db, assignment, current_user)
    audit.record_audit(db, action="assignment.pushed_to_gradebook", current_user=current_user, entity_type="assignment", entity_id=assignment.id, details=result)
    db.commit()
    return result


# --------------------------------------------------------------------------- #
# Student / parent
# --------------------------------------------------------------------------- #
@router.get("/mine")
def my_assignments(student_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Student/parent view: assignments for the (resolved) student's class,
    each with the student's own submission status and score."""
    profile = _student_profile(db, current_user, student_id)
    if not profile.current_class_id:
        return []
    rows = db.query(models.Assignment).filter(
        models.Assignment.class_id == profile.current_class_id,
        models.Assignment.status == models.AssignmentStatus.PUBLISHED,
    ).order_by(models.Assignment.due_date.asc().nullslast(), models.Assignment.created_at.desc()).all()
    subs = {
        s.assignment_id: s
        for s in db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.student_id == profile.id).all()
    }
    result = []
    for a in rows:
        if a.target_student_ids and profile.id not in set(a.target_student_ids):
            continue
        sub = subs.get(a.id)
        key_visible = svc.answer_key_visible_to_student(a)
        result.append({
            **_assignment_public(a, include_answer_key=key_visible),
            "submission": None if not sub else {
                "id": sub.id, "status": sub.workflow_status, "score": sub.score,
                "feedback": sub.feedback, "is_late": sub.is_late, "answers": sub.answers,
                "attachment_urls": sub.attachment_urls, "submitted_at": sub.submitted_at,
            },
            "answer_key_visible": key_visible,
        })
    return result


@router.post("/{assignment_id}/autosave")
def autosave_submission(assignment_id: int, payload: AutosaveRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in STUDENT_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux élèves.")
    profile = _student_profile(db, current_user, None)
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Devoir introuvable.")
    sub = svc.autosave(db, assignment, profile, answers=payload.answers, content_text=payload.content_text)
    db.commit()
    return {"submission_id": sub.id, "status": sub.workflow_status}


@router.post("/{assignment_id}/submit")
def submit_assignment(assignment_id: int, payload: SubmitRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in STUDENT_ROLES:
        raise HTTPException(status_code=403, detail="Réservé aux élèves.")
    profile = _student_profile(db, current_user, None)
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Devoir introuvable.")
    sub = svc.submit(db, assignment, profile, answers=payload.answers, content_text=payload.content_text, attachment_urls=payload.attachment_urls)
    audit.record_audit(db, action="assignment.submitted", current_user=current_user, entity_type="assignment", entity_id=assignment.id)
    db.commit()
    return {"submission_id": sub.id, "status": sub.workflow_status, "is_late": sub.is_late}
