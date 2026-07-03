import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations
from backend.services import ai_credits, remediation


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    return school


def _user(db, school, role, credits=0):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"{role.value}_{tag}@example.com", hashed_password="x", full_name=f"{role.value} {tag}", role=role, school_id=school.id, is_active=True)
    db.add(user); db.commit()
    if credits:
        wallet = ai_credits.wallet_for_user(db, user)
        wallet.balance_credits = credits
        db.commit()
    return user


def _assessment_with_grades(db, school, scores):
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
    db.add(assessment); db.flush()
    profiles = []
    for score in scores:
        stag = uuid.uuid4().hex[:5]
        user = models.User(email=f"stu_{stag}@example.com", hashed_password="x", full_name=f"Student {stag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
        db.add(user); db.flush()
        profile = models.StudentProfile(user_id=user.id, registration_number=f"R{stag}", current_class_id=cls.id)
        db.add(profile); db.flush()
        db.add(models.Grade(score=score, assessment_id=assessment.id, student_id=profile.id))
        profiles.append(profile)
    db.commit()
    return assessment, profiles


def test_remediation_targets_struggling_students_only():
    db = _session()
    school = _school(db)
    teacher = _user(db, school, models.UserRole.TEACHER, credits=1000)
    assessment, profiles = _assessment_with_grades(db, school, scores=[4, 8, 15])

    summary = remediation.run_remediation(db, assessment.id, school.id, teacher)
    db.commit()

    assert summary["graded"] == 3 and summary["above_threshold"] == 1
    assert len(summary["generated"]) == 2
    assert all(item["practice_set"] for item in summary["generated"])

    notifs = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "remediation.assigned").all()
    assert len(notifs) == 2
    assert {n.student_id for n in notifs} == {profiles[0].id, profiles[1].id}
    assert all(n.source_type == "assessment" and n.source_id == assessment.id for n in notifs)


def test_remediation_rerun_only_serves_new_grades():
    db = _session()
    school = _school(db)
    teacher = _user(db, school, models.UserRole.TEACHER, credits=1000)
    assessment, _profiles = _assessment_with_grades(db, school, scores=[3])

    first = remediation.run_remediation(db, assessment.id, school.id, teacher)
    db.commit()
    assert len(first["generated"]) == 1

    second = remediation.run_remediation(db, assessment.id, school.id, teacher)
    db.commit()
    assert len(second["generated"]) == 0 and second["skipped_done"] == 1

    # A newly graded struggling student gets served on the next run.
    stag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{stag}@example.com", hashed_password="x", full_name="New", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{stag}")
    db.add(profile); db.flush()
    db.add(models.Grade(score=2, assessment_id=assessment.id, student_id=profile.id))
    db.commit()

    third = remediation.run_remediation(db, assessment.id, school.id, teacher)
    db.commit()
    assert len(third["generated"]) == 1 and third["skipped_done"] == 1


def test_remediation_tenant_scope_and_rbac():
    db = _session()
    school_a = _school(db)
    school_b = _school(db)
    teacher_a = _user(db, school_a, models.UserRole.TEACHER, credits=1000)
    assessment_b, _ = _assessment_with_grades(db, school_b, scores=[2])

    try:
        remediation.run_remediation(db, assessment_b.id, school_a.id, teacher_a)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404

    student = _user(db, school_a, models.UserRole.STUDENT)
    try:
        automations.remediation_run(assessment_id=assessment_b.id, threshold_ratio=0.5, language="fr", school_id=None, db=db, current_user=student)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403


def test_assessment_stats_listing():
    db = _session()
    school = _school(db)
    teacher = _user(db, school, models.UserRole.TEACHER, credits=1000)
    _assessment_with_grades(db, school, scores=[4, 16])

    rows = automations.remediation_assessments(limit=30, school_id=None, db=db, current_user=teacher)
    assert len(rows) == 1
    assert rows[0]["grades"] == 2 and rows[0]["struggling"] == 1 and rows[0]["average"] == 10.0
