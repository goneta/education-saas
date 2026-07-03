import uuid
from datetime import datetime, time, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations
from backend.services import absence_followup, anomaly_digest


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


def _student(db, school, parent_phone=None, with_parent_user=False, class_id=None):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}", parent_phone=parent_phone, parent_name="Parent", current_class_id=class_id)
    db.add(profile); db.flush()
    parent = None
    if with_parent_user:
        parent = models.User(email=f"par_{tag}@example.com", hashed_password="x", full_name=f"Parent {tag}", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
        db.add(parent); db.flush()
        db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=profile.id, is_active=True))
    db.commit()
    return profile, parent


def _timetable(db, school):
    tag = uuid.uuid4().hex[:4]
    cls = models.Class(name=f"C{tag}", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"Maths {tag}", school_id=school.id)
    db.add(subject); db.flush()
    timetable = models.Timetable(class_id=cls.id, subject_id=subject.id, day_of_week=models.DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(9, 0))
    db.add(timetable); db.commit()
    return timetable


def _absence(db, profile, timetable, days_ago=0, status=models.AttendanceStatus.ABSENT):
    row = models.Attendance(date=datetime.utcnow() - timedelta(days=days_ago), status=status, student_id=profile.id, timetable_id=timetable.id)
    db.add(row); db.commit()
    return row


def test_absence_followup_notifies_parent_and_queues_sms_once():
    db = _session()
    school, admin = _school_admin(db)
    profile, parent = _student(db, school, parent_phone="+22501020304", with_parent_user=True)
    timetable = _timetable(db, school)
    _absence(db, profile, timetable)

    first = absence_followup.run_absence_followup(db, school.id, admin)
    db.commit()
    assert first["notified"] == 1 and first["sms_queued"] == 1

    notif = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "absence.followup").one()
    assert notif.recipient_user_id == parent.id and "Maths" in notif.message
    assert db.query(models.SmsMessage).count() == 1

    second = absence_followup.run_absence_followup(db, school.id, admin)
    db.commit()
    assert second["notified"] == 0 and second["skipped_done"] == 1


def test_absence_followup_skips_without_contact_and_present_rows():
    db = _session()
    school, admin = _school_admin(db)
    orphan, _ = _student(db, school)  # no parent link, no phone
    timetable = _timetable(db, school)
    _absence(db, orphan, timetable)
    _absence(db, orphan, timetable, status=models.AttendanceStatus.PRESENT)  # not scanned

    summary = absence_followup.run_absence_followup(db, school.id, admin)
    db.commit()
    assert summary["scanned"] == 1 and summary["skipped_no_contact"] == 1 and summary["notified"] == 0


def test_anomaly_digest_flags_and_cooldown():
    db = _session()
    school, admin = _school_admin(db)
    timetable = _timetable(db, school)

    # Class-size imbalance: 4 vs 1 students on two classes.
    cls_a = models.Class(name="A", school_id=school.id); cls_b = models.Class(name="B", school_id=school.id)
    db.add_all([cls_a, cls_b]); db.commit()
    profiles = [_student(db, school, class_id=cls_a.id)[0] for _ in range(4)]
    _student(db, school, class_id=cls_b.id)

    # Absence spike: 6 absences this window, none before.
    for profile in profiles:
        _absence(db, profile, timetable)
    _absence(db, profiles[0], timetable)
    _absence(db, profiles[1], timetable)

    # Unpaid ratio: 100% outstanding.
    db.add(models.Fee(title="F", amount=50000, due_date=datetime.utcnow(), status=models.FeeStatus.PENDING, student_id=profiles[0].id, school_id=school.id))
    db.commit()

    summary = anomaly_digest.run_anomaly_digest(db, school.id, admin)
    db.commit()
    assert summary["absence_spike"] is True
    assert summary["unpaid_flag"] is True and summary["unpaid_ratio"] == 1.0
    assert summary["imbalance_flag"] is True and summary["anomalies"] == 3

    digest = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "anomaly.digest").one()
    assert digest.recipient_user_id == admin.id and "Pic d'absences" in digest.message

    again = anomaly_digest.run_anomaly_digest(db, school.id, admin)
    db.commit()
    assert again["skipped_cooldown"] is True and again["notified"] == 0


def test_anomaly_digest_quiet_school_reports_no_anomaly():
    db = _session()
    school, admin = _school_admin(db)

    summary = anomaly_digest.run_anomaly_digest(db, school.id, admin)
    db.commit()
    assert summary["anomalies"] == 0 and summary["notified"] == 1
    digest = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "anomaly.digest").one()
    assert "Aucune anomalie" in digest.message


def test_endpoint_rbac_and_generic_history():
    db = _session()
    school, admin = _school_admin(db)
    teacher = models.User(email=f"t_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.commit()

    for fn, kwargs in [
        (automations.run_absence_followup, {"days": 2}),
        (automations.run_anomaly_digest, {"days": 7, "unpaid_threshold": 0.3}),
    ]:
        try:
            fn(school_id=None, db=db, current_user=teacher, **kwargs)
            assert False
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 403

    automations.run_anomaly_digest(days=7, unpaid_threshold=0.3, school_id=None, db=db, current_user=admin)
    rows = automations.automation_notification_history(event_type="anomaly.digest", limit=50, school_id=None, db=db, current_user=admin)
    assert len(rows) == 1 and rows[0].event_type == "anomaly.digest"
