import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import ai_learning


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _user(db, role):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"L {uid}", domain_prefix=f"l_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    user = models.User(email=f"u_{uid}@l.local", hashed_password="x", full_name="U", role=role, school_id=school.id, is_active=True)
    db.add(user); db.commit()
    return user


def test_teacher_generates_lesson_quiz_exam_and_audited():
    db = _session()
    teacher = _user(db, models.UserRole.TEACHER)
    lesson = ai_learning.generate_lesson(ai_learning.LessonRequest(subject="Maths", level="6e", topic="Fractions"), db=db, current_user=teacher)
    assert lesson["kind"] == "lesson" and lesson["content"]
    quiz = ai_learning.generate_quiz(ai_learning.QuizRequest(subject="Maths", topic="Fractions", num_questions=3), db=db, current_user=teacher)
    assert quiz["kind"] == "quiz" and quiz["content"]
    exam = ai_learning.generate_exam(ai_learning.ExamRequest(subject="Maths", level="6e", topics="Fractions, Decimals"), db=db, current_user=teacher)
    assert exam["kind"] == "exam" and exam["content"]
    # Each generation is audit-logged.
    assert db.query(models.AuditLog).filter(models.AuditLog.action.like("ai_learning.%")).count() == 3


def test_student_cannot_generate():
    db = _session()
    student = _user(db, models.UserRole.STUDENT)
    try:
        ai_learning.generate_quiz(ai_learning.QuizRequest(subject="X", topic="Y"), db=db, current_user=student)
        assert False, "student must not generate content"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
