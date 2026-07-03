import uuid
from datetime import datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    return school


def _family_with_absence(db, school, status=models.AttendanceStatus.ABSENT):
    tag = uuid.uuid4().hex[:5]
    student_user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student_user); db.flush()
    profile = models.StudentProfile(user_id=student_user.id, registration_number=f"R{tag}")
    db.add(profile); db.flush()
    parent = models.User(email=f"par_{tag}@example.com", hashed_password="x", full_name=f"Parent {tag}", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.flush()
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=profile.id, is_active=True))
    teacher = models.User(email=f"t_{tag}@example.com", hashed_password="x", full_name=f"Teacher {tag}", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.flush()
    cls = models.Class(name=f"C{tag}", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"Sub{tag}", school_id=school.id)
    db.add(subject); db.flush()
    timetable = models.Timetable(class_id=cls.id, subject_id=subject.id, day_of_week=models.DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(9, 0))
    db.add(timetable); db.flush()
    attendance = models.Attendance(date=datetime.utcnow() - timedelta(days=1), status=status, student_id=profile.id, timetable_id=timetable.id, recorded_by_id=teacher.id)
    db.add(attendance); db.commit()
    return parent, teacher, attendance


def test_parent_justifies_absence_one_tap():
    db = _session()
    school = _school(db)
    parent, teacher, attendance = _family_with_absence(db, school)

    result = automations.justify_absence(attendance_id=attendance.id, reason="Rendez-vous médical", db=db, current_user=parent)
    assert result["status"] == "excused"

    db.refresh(attendance)
    assert attendance.status == models.AttendanceStatus.EXCUSED
    assert "Justifiée par le parent" in attendance.remarks and "Rendez-vous médical" in attendance.remarks

    notif = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "absence.justified").one()
    assert notif.recipient_user_id == teacher.id and notif.source_id == attendance.id


def test_justify_guards():
    db = _session()
    school = _school(db)
    parent, _teacher, attendance = _family_with_absence(db, school)

    # Already excused -> 409 on a second tap.
    automations.justify_absence(attendance_id=attendance.id, reason="", db=db, current_user=parent)
    try:
        automations.justify_absence(attendance_id=attendance.id, reason="", db=db, current_user=parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 409

    # An unlinked parent cannot justify.
    other_parent, _t2, other_attendance = _family_with_absence(db, school)
    try:
        automations.justify_absence(attendance_id=other_attendance.id, reason="", db=db, current_user=parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403

    # Non-parents are refused; unknown attendance -> 404.
    student = models.User(email=f"s_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student); db.commit()
    try:
        automations.justify_absence(attendance_id=other_attendance.id, reason="", db=db, current_user=student)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403
    try:
        automations.justify_absence(attendance_id=999999, reason="", db=db, current_user=other_parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404


def test_present_row_cannot_be_justified():
    db = _session()
    school = _school(db)
    parent, _teacher, attendance = _family_with_absence(db, school, status=models.AttendanceStatus.PRESENT)
    try:
        automations.justify_absence(attendance_id=attendance.id, reason="", db=db, current_user=parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 409
