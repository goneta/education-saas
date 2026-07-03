import uuid
from datetime import datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations
from backend.services import student_planner


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_admin(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{tag}@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, admin


def _class_with_subject(db, school):
    tag = uuid.uuid4().hex[:4]
    cls = models.Class(name=f"C{tag}", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"Maths {tag}", school_id=school.id)
    db.add(subject); db.commit()
    return cls, subject


def _student(db, school, cls):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}", current_class_id=cls.id)
    db.add(profile); db.commit()
    return user, profile


def _term(db, school):
    year = models.AcademicYear(name=f"Y{uuid.uuid4().hex[:4]}", school_id=school.id, is_current=True,
                               start_date=datetime.utcnow() - timedelta(days=100), end_date=datetime.utcnow() + timedelta(days=200))
    db.add(year); db.flush()
    term = models.Term(name="T1", academic_year_id=year.id, start_date=year.start_date, end_date=year.end_date)
    db.add(term); db.commit()
    return term


def test_study_plan_compiles_assessments_homework_and_slots():
    db = _session()
    school, _admin = _school_admin(db)
    cls, subject = _class_with_subject(db, school)
    user, profile = _student(db, school, cls)
    term = _term(db, school)

    assessment = models.Assessment(title="Contrôle", date=datetime.utcnow() + timedelta(days=7), max_score=20,
                                   class_id=cls.id, subject_id=subject.id, term_id=term.id)
    db.add(assessment)
    db.add(models.Assignment(title="Exercices ch.3", due_date=datetime.utcnow() + timedelta(days=4),
                             status=models.AssignmentStatus.PUBLISHED, class_id=cls.id, subject_id=subject.id, school_id=school.id))
    db.add(models.Timetable(class_id=cls.id, subject_id=subject.id, day_of_week=models.DayOfWeek.MONDAY,
                            start_time=time(8, 0), end_time=time(9, 0)))
    db.commit()

    plan = automations.study_plan(student_id=None, horizon_days=21, db=db, current_user=user)
    assert len(plan["assessments"]) == 1 and plan["assessments"][0]["title"] == "Contrôle"
    assert len(plan["homework"]) == 1 and plan["homework"][0]["title"] == "Exercices ch.3"
    steps = [slot["step"] for slot in plan["revision_slots"]]
    assert steps == ["overview", "practice", "final_review"]  # D-5, D-2, D-1, chronological
    assert len(plan["timetable"]) == 1


def test_study_plan_excludes_submitted_homework_and_parent_access():
    db = _session()
    school, _admin = _school_admin(db)
    cls, subject = _class_with_subject(db, school)
    user, profile = _student(db, school, cls)
    assignment = models.Assignment(title="Rendu", due_date=datetime.utcnow() + timedelta(days=3),
                                   status=models.AssignmentStatus.PUBLISHED, class_id=cls.id, subject_id=subject.id, school_id=school.id)
    db.add(assignment); db.flush()
    db.add(models.AssignmentSubmission(assignment_id=assignment.id, student_id=profile.id))
    parent = models.User(email=f"p_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="P", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.flush()
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=profile.id, is_active=True))
    db.commit()

    plan = automations.study_plan(student_id=None, horizon_days=21, db=db, current_user=user)
    assert plan["homework"] == []  # submitted → not pending

    as_parent = automations.study_plan(student_id=profile.id, horizon_days=21, db=db, current_user=parent)
    assert as_parent["homework"] == []

    try:
        automations.study_plan(student_id=999999, horizon_days=21, db=db, current_user=parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403


def test_homework_reminders_buckets_and_idempotence():
    db = _session()
    school, admin = _school_admin(db)
    cls, subject = _class_with_subject(db, school)
    _u1, p1 = _student(db, school, cls)
    _u2, p2 = _student(db, school, cls)
    assignment = models.Assignment(title="DM", due_date=datetime.utcnow() + timedelta(days=2, hours=12),
                                   status=models.AssignmentStatus.PUBLISHED, class_id=cls.id, subject_id=subject.id, school_id=school.id)
    db.add(assignment); db.flush()
    db.add(models.AssignmentSubmission(assignment_id=assignment.id, student_id=p2.id))  # p2 already submitted
    db.commit()

    first = student_planner.run_homework_reminders(db, school.id, admin)
    db.commit()
    assert first["reminders"] == 1 and first["skipped_submitted"] == 1

    rows = db.query(models.NotificationHistory).all()
    assert len(rows) == 1 and rows[0].event_type == "homework.reminder.d3" and rows[0].student_id == p1.id

    second = student_planner.run_homework_reminders(db, school.id, admin)
    db.commit()
    assert second["reminders"] == 0 and second["skipped_sent"] == 1


def test_homework_reminders_far_due_dates_ignored_and_rbac():
    db = _session()
    school, admin = _school_admin(db)
    cls, subject = _class_with_subject(db, school)
    _student(db, school, cls)
    db.add(models.Assignment(title="Loin", due_date=datetime.utcnow() + timedelta(days=20),
                             status=models.AssignmentStatus.PUBLISHED, class_id=cls.id, subject_id=subject.id, school_id=school.id))
    db.commit()

    summary = student_planner.run_homework_reminders(db, school.id, admin)
    db.commit()
    assert summary["assignments"] == 0 and summary["reminders"] == 0

    teacher = models.User(email=f"t_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.commit()
    try:
        automations.run_homework_reminders(school_id=None, db=db, current_user=teacher)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403
    try:
        automations.study_plan(student_id=None, horizon_days=21, db=db, current_user=teacher)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403
