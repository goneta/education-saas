import uuid
from datetime import datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations
from backend.services import ai_credits, sequence_builder


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    return school


def _teacher(db, school, credits=1000):
    tag = uuid.uuid4().hex[:5]
    teacher = models.User(email=f"t_{tag}@example.com", hashed_password="x", full_name=f"T {tag}", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.commit()
    if credits:
        wallet = ai_credits.wallet_for_user(db, teacher)
        wallet.balance_credits = credits
        db.commit()
    return teacher


def _pair_with_slots(db, school, slots=2):
    tag = uuid.uuid4().hex[:4]
    cls = models.Class(name=f"C{tag}", level="6EME", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"Maths {tag}", school_id=school.id)
    db.add(subject); db.flush()
    days = [models.DayOfWeek.MONDAY, models.DayOfWeek.THURSDAY, models.DayOfWeek.FRIDAY]
    for index in range(slots):
        db.add(models.Timetable(class_id=cls.id, subject_id=subject.id, day_of_week=days[index % 3],
                                start_time=time(8, 0), end_time=time(9, 0)))
    db.commit()
    return cls, subject


def _term(db, school, weeks=10):
    year = models.AcademicYear(name=f"Y{uuid.uuid4().hex[:4]}", school_id=school.id, is_current=True,
                               start_date=datetime.utcnow() - timedelta(days=30), end_date=datetime.utcnow() + timedelta(days=300))
    db.add(year); db.flush()
    term = models.Term(name="T1", academic_year_id=year.id, start_date=datetime.utcnow(),
                       end_date=datetime.utcnow() + timedelta(weeks=weeks))
    db.add(term); db.commit()
    return term


def test_options_report_weekly_slots_and_terms():
    db = _session()
    school = _school(db)
    teacher = _teacher(db, school)
    cls, subject = _pair_with_slots(db, school, slots=3)
    _term(db, school)

    options = automations.sequence_options(school_id=None, db=db, current_user=teacher)
    assert len(options["pairs"]) == 1
    pair = options["pairs"][0]
    assert pair["class_id"] == cls.id and pair["subject_id"] == subject.id
    assert pair["weekly_slots"] == 3 and pair["weekly_minutes"] == 180
    assert len(options["terms"]) == 1


def test_build_sequence_computes_sessions_and_notifies():
    db = _session()
    school = _school(db)
    teacher = _teacher(db, school)
    cls, subject = _pair_with_slots(db, school, slots=2)
    term = _term(db, school, weeks=10)

    result = sequence_builder.build_sequence(db, school.id, teacher, class_id=cls.id, subject_id=subject.id, term_id=term.id, topic="Fractions")
    db.commit()

    assert result["weekly_slots"] == 2 and result["weeks"] == 10 and result["sessions"] == 20
    assert result["sequence"]
    notif = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "sequence.generated").one()
    assert notif.recipient_user_id == teacher.id and notif.source_id == cls.id


def test_build_sequence_guards():
    db = _session()
    school_a = _school(db)
    school_b = _school(db)
    teacher_a = _teacher(db, school_a)
    cls_b, subject_b = _pair_with_slots(db, school_b)
    term_b = _term(db, school_b)

    # Another school's class -> 404.
    try:
        sequence_builder.build_sequence(db, school_a.id, teacher_a, class_id=cls_b.id, subject_id=subject_b.id, term_id=term_b.id)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404

    # A pair without timetable slots -> 422.
    cls_a = models.Class(name="CA", school_id=school_a.id)
    db.add(cls_a); db.flush()
    subject_a = models.Subject(name="Hist", school_id=school_a.id)
    db.add(subject_a); db.commit()
    try:
        sequence_builder.build_sequence(db, school_a.id, teacher_a, class_id=cls_a.id, subject_id=subject_a.id, term_id=term_b.id)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 422

    # Students cannot use the endpoints.
    student = models.User(email=f"s_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school_a.id, is_active=True)
    db.add(student); db.commit()
    try:
        automations.sequence_options(school_id=None, db=db, current_user=student)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403
