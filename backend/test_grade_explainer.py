import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations
from backend.services import ai_credits, grade_explainer


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    return school


def _student(db, school, credits=0):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}")
    db.add(profile); db.commit()
    if credits:
        wallet = ai_credits.wallet_for_user(db, user)
        wallet.balance_credits = credits
        db.commit()
    return user, profile


def _assessment(db, school):
    tag = uuid.uuid4().hex[:4]
    cls = models.Class(name=f"C{tag}", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"Maths {tag}", school_id=school.id)
    db.add(subject); db.flush()
    year = models.AcademicYear(name=f"Y{tag}", school_id=school.id, is_current=True,
                               start_date=datetime.utcnow() - timedelta(days=100), end_date=datetime.utcnow() + timedelta(days=200))
    db.add(year); db.flush()
    term = models.Term(name="T1", academic_year_id=year.id, start_date=year.start_date, end_date=year.end_date)
    db.add(term); db.flush()
    assessment = models.Assessment(title=f"Contrôle {tag}", date=datetime.utcnow() - timedelta(days=1), max_score=20,
                                   class_id=cls.id, subject_id=subject.id, term_id=term.id)
    db.add(assessment); db.commit()
    return assessment


def _grade(db, assessment, profile, score, comment=None):
    grade = models.Grade(score=score, comment=comment, assessment_id=assessment.id, student_id=profile.id)
    db.add(grade); db.commit()
    return grade


def test_grades_listing_includes_class_stats():
    db = _session()
    school = _school(db)
    user, profile = _student(db, school)
    _other_user, other_profile = _student(db, school)
    assessment = _assessment(db, school)
    _grade(db, assessment, profile, 12, comment="Bon raisonnement")
    _grade(db, assessment, other_profile, 16)

    rows = automations.explain_grade_grades(student_id=None, limit=20, db=db, current_user=user)
    assert len(rows) == 1
    row = rows[0]
    assert row["score"] == 12 and row["class_average"] == 14.0 and row["class_best"] == 16
    assert row["class_size"] == 2 and row["comment"] == "Bon raisonnement"


def test_explain_returns_walkthrough_with_rank():
    db = _session()
    school = _school(db)
    user, profile = _student(db, school, credits=1000)
    _u2, p2 = _student(db, school)
    _u3, p3 = _student(db, school)
    assessment = _assessment(db, school)
    grade = _grade(db, assessment, profile, 10)
    _grade(db, assessment, p2, 15)
    _grade(db, assessment, p3, 5)

    result = grade_explainer.explain_grade(db, grade.id, profile, user)
    assert result["rank"] == 2 and result["class_size"] == 3
    assert result["class_average"] == 10.0 and result["class_best"] == 15
    assert result["explanation"]


def test_explain_denies_other_students_grade_and_unlinked_parent():
    db = _session()
    school = _school(db)
    user, profile = _student(db, school, credits=1000)
    _other_user, other_profile = _student(db, school)
    assessment = _assessment(db, school)
    other_grade = _grade(db, assessment, other_profile, 8)

    try:
        grade_explainer.explain_grade(db, other_grade.id, profile, user)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404

    parent = models.User(email=f"p_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="P", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.commit()
    try:
        automations.explain_grade_run(grade_id=other_grade.id, student_id=other_profile.id, language="fr", db=db, current_user=parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403  # no ParentStudentLink

    teacher = models.User(email=f"t_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.commit()
    try:
        automations.explain_grade_grades(student_id=None, limit=20, db=db, current_user=teacher)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403


def test_linked_parent_can_explain_childs_grade():
    db = _session()
    school = _school(db)
    _user, profile = _student(db, school)
    assessment = _assessment(db, school)
    grade = _grade(db, assessment, profile, 9)
    parent = models.User(email=f"p_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="P", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.flush()
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=profile.id, is_active=True))
    db.commit()
    wallet = ai_credits.wallet_for_user(db, parent)
    wallet.balance_credits = 1000
    db.commit()

    result = automations.explain_grade_run(grade_id=grade.id, student_id=profile.id, language="en", db=db, current_user=parent)
    assert result["grade_id"] == grade.id and result["explanation"]
