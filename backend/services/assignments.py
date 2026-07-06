"""Homework / exercise module — the core service.

Covers the full pedagogical loop on the existing `Assignment` /
`AssignmentSubmission` tables (extended in migration 0050):

- creation (manual + AI-generated with an auto-produced answer key / corrigé),
- two delivery modes (online and paper),
- student submissions (online answers + file attachments, drafts, attempts,
  late handling, lock after due date),
- grading (manual + AI grading against the answer key, teacher always overrides),
- answer-key access control (never / after-due / immediate),
- a bridge into the gradebook (creates an Assessment + Grade rows),
- roster/status views and per-assignment statistics,
- notifications on publish / submit / grade.

AI generations are credit-gated on the caller; nothing is faked — when no AI
provider is reachable the generator raises and the caller surfaces the error.
"""

import json
import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..services.ai_service import ai_service
from . import ai_credits, automation

ASSIGNMENT_TYPES = {
    "devoir", "exercice", "interrogation", "controle", "evaluation", "examen",
    "quiz", "devoir_maison", "tp", "projet", "expose",
}
QUESTION_TYPES = {
    "open", "mcq", "true_false", "short_answer", "long_answer", "fill_blank",
    "matching", "ordering", "calculation", "problem", "case_study",
    "programming", "essay", "reading_comprehension",
}
EDITABLE_STATES = ("draft",)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _now() -> datetime:
    return datetime.utcnow()


def _parse_json_object(content: str) -> dict:
    """Tolerant extraction of a JSON object from an AI response."""
    match = re.search(r"\{.*\}", content or "", flags=re.DOTALL)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def teacher_assignment_or_404(db: Session, assignment_id: int, school_id: int) -> models.Assignment:
    row = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id,
        models.Assignment.school_id == school_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Devoir introuvable dans votre établissement.")
    return row


def roster(db: Session, assignment: models.Assignment) -> list:
    """Active students the assignment targets (whole class or a subset)."""
    query = (
        db.query(models.StudentProfile, models.User)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(models.StudentProfile.current_class_id == assignment.class_id, models.User.is_active == True)  # noqa: E712
    )
    profiles = query.all()
    targets = assignment.target_student_ids or None
    if targets:
        targets = set(targets)
        profiles = [(p, u) for p, u in profiles if p.id in targets]
    return profiles


def _student_targeted(assignment: models.Assignment, profile: models.StudentProfile) -> bool:
    if profile.current_class_id != assignment.class_id:
        return False
    return not assignment.target_student_ids or profile.id in set(assignment.target_student_ids)


# --------------------------------------------------------------------------- #
# Creation
# --------------------------------------------------------------------------- #
def create_assignment(db: Session, teacher: models.User, school_id: int, *, payload: dict) -> models.Assignment:
    assignment_type = (payload.get("assignment_type") or "devoir").lower()
    if assignment_type not in ASSIGNMENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Type de devoir invalide : {assignment_type}.")
    mode = (payload.get("mode") or "online").lower()
    if mode not in ("online", "paper"):
        raise HTTPException(status_code=422, detail="Mode invalide (online|paper).")
    cls = db.query(models.Class).filter(models.Class.id == payload.get("class_id"), models.Class.school_id == school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Classe introuvable dans votre établissement.")

    row = models.Assignment(
        title=(payload.get("title") or "").strip() or "Devoir sans titre",
        instructions=payload.get("instructions"),
        assignment_type=assignment_type,
        mode=mode,
        content=payload.get("content"),
        answer_key=payload.get("answer_key"),
        max_score=float(payload.get("max_score") or 20),
        class_id=cls.id,
        subject_id=payload.get("subject_id"),
        teacher_id=teacher.id,
        school_id=school_id,
        status=models.AssignmentStatus.DRAFT,
        open_at=payload.get("open_at"),
        due_date=payload.get("due_date"),
        duration_minutes=payload.get("duration_minutes"),
        max_attempts=int(payload.get("max_attempts") or 1),
        late_penalty=float(payload.get("late_penalty") or 0),
        allow_groups=bool(payload.get("allow_groups")),
        target_student_ids=payload.get("target_student_ids") or None,
        answer_key_release=payload.get("answer_key_release") or "after_due",
        ai_generated=bool(payload.get("ai_generated")),
    )
    db.add(row)
    db.flush()
    return row


def generate_ai(db: Session, teacher: models.User, *, subject: str, level: str, chapter: str = "",
                skills: str = "", assignment_type: str = "devoir", difficulty: str = "moyen",
                num_questions: int = 8, question_types: str = "", language: str = "fr") -> dict:
    """AI-generate an assignment's questions AND its answer key (corrigé)."""
    prompt = (
        f"Create in {language} a school {assignment_type} for subject '{subject}', level '{level}'"
        f"{f', chapter/topic: {chapter}' if chapter else ''}"
        f"{f', target skills: {skills}' if skills else ''}. "
        f"Difficulty: {difficulty}. Produce {num_questions} questions"
        f"{f' of types: {question_types}' if question_types else ' mixing question types'}. "
        "Return ONLY a JSON object of the exact shape: "
        '{"questions":[{"id":1,"type":"mcq|open|true_false|short_answer|long_answer|fill_blank|matching|ordering|calculation|problem|case_study|programming|essay|reading_comprehension",'
        '"prompt":"…","options":["…"] (mcq only),"points":2,"expected_answer":"…","explanation":"…","skill":"…"}], '
        '"rubric":"grading criteria","total_points":20}. '
        "No commentary, no markdown fences."
    )
    ai_credits.ensure_credits(db, teacher, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "assignment_generation"}, db)
    raw = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, teacher, prompt, raw if isinstance(raw, str) else json.dumps(raw), "assignment_generation", "generate")
    data = raw if isinstance(raw, dict) else _parse_json_object(raw)
    questions = data.get("questions") if isinstance(data, dict) else None
    if not questions:
        raise HTTPException(status_code=502, detail="La génération IA n'a pas renvoyé de questions exploitables. Réessayez.")

    # Split into a student-safe content (no answers) and the answer key (corrigé).
    student_questions, key_items, total = [], [], 0
    for index, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            continue
        qid = q.get("id") or index
        points = q.get("points") or 0
        total += points if isinstance(points, (int, float)) else 0
        student_questions.append({
            "id": qid, "type": q.get("type") or "open", "prompt": q.get("prompt") or "",
            "options": q.get("options") or None, "points": points,
        })
        key_items.append({
            "id": qid, "expected_answer": q.get("expected_answer") or "",
            "explanation": q.get("explanation") or "", "points": points, "skill": q.get("skill") or "",
        })
    content = {"questions": student_questions}
    answer_key = {"items": key_items, "rubric": data.get("rubric") or "", "total_points": total}
    return {"content": content, "answer_key": answer_key, "max_score": total or 20, "model_name": result.get("model_name")}


def publish(db: Session, assignment: models.Assignment, teacher: models.User) -> models.Assignment:
    assignment.status = models.AssignmentStatus.PUBLISHED
    if not assignment.open_at:
        assignment.open_at = _now()
    for profile, user in roster(db, assignment):
        automation.record_notification(
            db,
            event_type="assignment.published",
            subject=f"Nouveau {assignment.assignment_type} : {assignment.title}",
            message=f"Un nouveau {assignment.assignment_type} « {assignment.title} » vous a été attribué"
                    + (f", à rendre le {assignment.due_date.strftime('%d/%m/%Y')}." if assignment.due_date else "."),
            school_id=assignment.school_id,
            student_id=profile.id,
            recipient_user=user,
            source_type="assignment",
            source_id=assignment.id,
            current_user=teacher,
        )
    return assignment


# --------------------------------------------------------------------------- #
# Student submissions
# --------------------------------------------------------------------------- #
def _get_or_create_submission(db: Session, assignment: models.Assignment, profile: models.StudentProfile) -> models.AssignmentSubmission:
    sub = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == assignment.id,
        models.AssignmentSubmission.student_id == profile.id,
    ).first()
    if not sub:
        sub = models.AssignmentSubmission(
            assignment_id=assignment.id, student_id=profile.id,
            workflow_status="draft", status=models.SubmissionStatus.SUBMITTED, attempt_number=1,
        )
        db.add(sub)
        db.flush()
    return sub


def open_submission(db: Session, assignment: models.Assignment, profile: models.StudentProfile) -> models.AssignmentSubmission:
    if assignment.status != models.AssignmentStatus.PUBLISHED:
        raise HTTPException(status_code=409, detail="Ce devoir n'est pas ouvert.")
    if not _student_targeted(assignment, profile):
        raise HTTPException(status_code=403, detail="Ce devoir ne vous est pas attribué.")
    return _get_or_create_submission(db, assignment, profile)


def autosave(db: Session, assignment: models.Assignment, profile: models.StudentProfile, *, answers: dict, content_text: str = None) -> models.AssignmentSubmission:
    sub = open_submission(db, assignment, profile)
    if sub.workflow_status in ("submitted", "graded", "returned"):
        raise HTTPException(status_code=409, detail="Ce devoir a déjà été remis.")
    sub.answers = answers
    if content_text is not None:
        sub.content_text = content_text
    return sub


def submit(db: Session, assignment: models.Assignment, profile: models.StudentProfile, *, answers: dict = None, content_text: str = None, attachment_urls: list = None) -> models.AssignmentSubmission:
    sub = open_submission(db, assignment, profile)
    if sub.workflow_status in ("submitted", "graded", "returned"):
        if sub.attempt_number >= (assignment.max_attempts or 1):
            raise HTTPException(status_code=409, detail="Nombre de tentatives épuisé.")
        sub.attempt_number += 1
    if assignment.due_date and _now() > assignment.due_date:
        # Locked after due unless late submissions are allowed via a late penalty.
        if not assignment.late_penalty:
            raise HTTPException(status_code=409, detail="La date limite est dépassée.")
        sub.is_late = True
    if answers is not None:
        sub.answers = answers
    if content_text is not None:
        sub.content_text = content_text
    if attachment_urls is not None:
        sub.attachment_urls = attachment_urls
    sub.workflow_status = "submitted"
    sub.status = models.SubmissionStatus.SUBMITTED
    sub.submitted_at = _now()

    teacher = db.query(models.User).filter(models.User.id == assignment.teacher_id).first()
    student_user = profile.user
    automation.record_notification(
        db,
        event_type="assignment.submitted",
        subject=f"Copie remise : {assignment.title}",
        message=f"{student_user.full_name if student_user else 'Un élève'} a remis « {assignment.title} »."
                + (" (en retard)" if sub.is_late else ""),
        school_id=assignment.school_id,
        student_id=profile.id,
        recipient_user=teacher,
        source_type="assignment",
        source_id=assignment.id,
        current_user=student_user,
    )
    return sub


# --------------------------------------------------------------------------- #
# Grading
# --------------------------------------------------------------------------- #
def _clamp_score(score: float, assignment: models.Assignment) -> float:
    return max(0.0, min(float(score), float(assignment.max_score or 20)))


def grade(db: Session, submission: models.AssignmentSubmission, teacher: models.User, *, score: float, feedback: str = None, annotations: list = None, publish_grade: bool = True) -> models.AssignmentSubmission:
    assignment = submission.assignment
    submission.score = _clamp_score(score, assignment)
    if assignment.late_penalty and submission.is_late:
        submission.score = max(0.0, submission.score - float(assignment.late_penalty))
    if feedback is not None:
        submission.feedback = feedback
    if annotations is not None:
        submission.annotations = annotations
    submission.graded_by_id = teacher.id
    submission.graded_at = _now()
    if publish_grade:
        submission.workflow_status = "graded"
        submission.status = models.SubmissionStatus.GRADED
        _notify_graded(db, submission, teacher)
    return submission


def ai_grade(db: Session, submission: models.AssignmentSubmission, teacher: models.User, *, language: str = "fr") -> dict:
    """AI-grade a submission against the assignment's answer key. Never final —
    the returned score/feedback are proposed on the submission (ai_graded) for
    the teacher to review, adjust and publish."""
    assignment = submission.assignment
    if not assignment.answer_key:
        raise HTTPException(status_code=422, detail="Ce devoir n'a pas de corrigé : la correction IA nécessite un corrigé.")
    answers = submission.answers or {}
    prompt = (
        f"You are a fair teacher grading a student's {assignment.assignment_type} in {language}, out of "
        f"{assignment.max_score}. Answer key (corrigé) as JSON: {json.dumps(assignment.answer_key, ensure_ascii=False)[:3000]}. "
        f"Student answers as JSON: {json.dumps(answers, ensure_ascii=False)[:3000]}. "
        f"{f'Student free text: {submission.content_text[:1500]}. ' if submission.content_text else ''}"
        "Grade strictly against the key. Return ONLY a JSON object: "
        '{"score":number (0..max),"feedback":"personalised comment","errors":["…"],"strengths":["…"],'
        '"weaknesses":["…"],"advice":["…"]}. No markdown.'
    )
    ai_credits.ensure_credits(db, teacher, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "assignment_grading"}, db)
    raw = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, teacher, prompt, raw if isinstance(raw, str) else json.dumps(raw), "assignment_grading", "ai_grade")
    data = raw if isinstance(raw, dict) else _parse_json_object(raw)
    try:
        proposed = _clamp_score(float(data.get("score")), assignment)
    except (TypeError, ValueError):
        raise HTTPException(status_code=502, detail="La correction IA n'a pas renvoyé de note exploitable.")

    submission.ai_graded = True
    submission.ai_feedback = {
        "score": proposed, "feedback": data.get("feedback") or "",
        "errors": data.get("errors") or [], "strengths": data.get("strengths") or [],
        "weaknesses": data.get("weaknesses") or [], "advice": data.get("advice") or [],
    }
    # Pre-fill the editable fields; the teacher confirms via grade(publish=True).
    submission.score = proposed
    submission.feedback = data.get("feedback") or submission.feedback
    submission.graded_by_id = teacher.id
    submission.graded_at = _now()
    return submission.ai_feedback


def _notify_graded(db: Session, submission: models.AssignmentSubmission, teacher: models.User) -> None:
    assignment = submission.assignment
    profile = submission.student
    student_user = profile.user if profile else None
    for recipient in _grade_recipients(db, profile, student_user):
        automation.record_notification(
            db,
            event_type="assignment.graded",
            subject=f"Correction disponible : {assignment.title}",
            message=f"« {assignment.title} » a été corrigé : {submission.score}/{assignment.max_score}."
                    + (f" {submission.feedback}" if submission.feedback else ""),
            school_id=assignment.school_id,
            student_id=profile.id if profile else None,
            recipient_user=recipient,
            source_type="assignment",
            source_id=assignment.id,
            current_user=teacher,
        )


def _grade_recipients(db: Session, profile, student_user) -> list:
    recipients = [u for u in [student_user] if u]
    if profile:
        links = db.query(models.ParentStudentLink).filter(
            models.ParentStudentLink.student_id == profile.id,
            models.ParentStudentLink.is_active == True,  # noqa: E712
        ).all()
        recipients += [link.parent for link in links if link.parent]
    return recipients


# --------------------------------------------------------------------------- #
# Answer-key access control
# --------------------------------------------------------------------------- #
def answer_key_visible_to_student(assignment: models.Assignment) -> bool:
    release = assignment.answer_key_release or "after_due"
    if release == "immediate":
        return True
    if release == "never":
        return False
    return bool(assignment.due_date and _now() > assignment.due_date)  # after_due


# --------------------------------------------------------------------------- #
# Gradebook bridge
# --------------------------------------------------------------------------- #
_TYPE_TO_ASSESSMENT = {
    "examen": models.AssessmentType.EXAM,
    "controle": models.AssessmentType.EXAM,
    "evaluation": models.AssessmentType.EXAM,
    "quiz": models.AssessmentType.QUIZ,
    "interrogation": models.AssessmentType.QUIZ,
    "projet": models.AssessmentType.PROJECT,
    "expose": models.AssessmentType.PROJECT,
}


def push_to_gradebook(db: Session, assignment: models.Assignment, teacher: models.User) -> dict:
    """Create/reuse an Assessment for this assignment and upsert Grade rows from
    the graded submissions, so assignment marks flow into the gradebook."""
    if not assignment.subject_id:
        raise HTTPException(status_code=422, detail="Associez une matière au devoir avant de l'envoyer au carnet de notes.")
    year = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == assignment.school_id,
        models.AcademicYear.is_current == True,  # noqa: E712
    ).first()
    term = db.query(models.Term).filter(models.Term.academic_year_id == year.id).order_by(models.Term.id.desc()).first() if year else None
    if not term:
        raise HTTPException(status_code=422, detail="Aucune période/trimestre courant pour créer l'évaluation.")

    assessment = db.query(models.Assessment).filter(
        models.Assessment.class_id == assignment.class_id,
        models.Assessment.subject_id == assignment.subject_id,
        models.Assessment.term_id == term.id,
        models.Assessment.title == assignment.title,
    ).first()
    if not assessment:
        assessment = models.Assessment(
            title=assignment.title,
            type=_TYPE_TO_ASSESSMENT.get(assignment.assignment_type, models.AssessmentType.HOMEWORK),
            date=assignment.due_date or _now(),
            max_score=int(assignment.max_score or 20),
            class_id=assignment.class_id, subject_id=assignment.subject_id, term_id=term.id,
        )
        db.add(assessment)
        db.flush()

    created, updated = 0, 0
    graded = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == assignment.id,
        models.AssignmentSubmission.workflow_status == "graded",
        models.AssignmentSubmission.score.isnot(None),
    ).all()
    for sub in graded:
        grade_row = db.query(models.Grade).filter(
            models.Grade.assessment_id == assessment.id,
            models.Grade.student_id == sub.student_id,
        ).first()
        if grade_row:
            grade_row.score = sub.score
            updated += 1
        else:
            db.add(models.Grade(assessment_id=assessment.id, student_id=sub.student_id, score=sub.score))
            created += 1
    return {"assessment_id": assessment.id, "created": created, "updated": updated}


# --------------------------------------------------------------------------- #
# Views & statistics
# --------------------------------------------------------------------------- #
def submission_roster(db: Session, assignment: models.Assignment) -> list:
    """Per-student status for the grading screen: submitted / late / absent."""
    subs = {
        s.student_id: s
        for s in db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.assignment_id == assignment.id).all()
    }
    rows = []
    for profile, user in roster(db, assignment):
        sub = subs.get(profile.id)
        rows.append({
            "student_id": profile.id,
            "student_name": user.full_name,
            "submission_id": sub.id if sub else None,
            "status": sub.workflow_status if sub else "absent",
            "is_late": bool(sub.is_late) if sub else False,
            "score": sub.score if sub else None,
            "ai_graded": bool(sub.ai_graded) if sub else False,
            "submitted_at": sub.submitted_at if (sub and sub.workflow_status != "draft") else None,
        })
    return rows


def stats(db: Session, assignment: models.Assignment) -> dict:
    roster_rows = roster(db, assignment)
    total = len(roster_rows)
    subs = db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.assignment_id == assignment.id).all()
    submitted = [s for s in subs if s.workflow_status in ("submitted", "graded", "returned")]
    graded = [s for s in subs if s.workflow_status == "graded" and s.score is not None]
    scores = [s.score for s in graded]
    average = round(sum(scores) / len(scores), 2) if scores else None
    max_score = assignment.max_score or 20
    pass_mark = 0.5 * max_score
    return {
        "students": total,
        "submitted": len(submitted),
        "missing": total - len({s.student_id for s in submitted}),
        "graded": len(graded),
        "late": sum(1 for s in submitted if s.is_late),
        "average": average,
        "success_rate": round(sum(1 for x in scores if x >= pass_mark) / len(scores) * 100, 1) if scores else None,
        "max_score": max_score,
    }
