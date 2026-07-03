import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import automations
from backend.services import fee_reminders


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


def _student(db, school, tag, parent_phone=None):
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}", parent_phone=parent_phone, parent_name="Parent")
    db.add(profile); db.flush()
    return user, profile


def _fee(db, school, profile, days_overdue, amount=10000, paid=0):
    fee = models.Fee(
        title=f"Scolarité {uuid.uuid4().hex[:4]}", amount=amount,
        due_date=datetime.now(timezone.utc) - timedelta(days=days_overdue),
        status=models.FeeStatus.PENDING, student_id=profile.id, school_id=school.id,
    )
    db.add(fee); db.flush()
    if paid:
        db.add(models.Payment(fee_id=fee.id, amount=paid, status="successful"))
    db.commit()
    return fee


def test_levels_channels_and_escalation():
    db = _session()
    school, admin = _school_admin(db)
    _u1, p1 = _student(db, school, uuid.uuid4().hex[:5], parent_phone="+22501020304")
    _u2, p2 = _student(db, school, uuid.uuid4().hex[:5])  # no parent phone
    fee_l1 = _fee(db, school, p1, days_overdue=2)
    fee_l2 = _fee(db, school, p2, days_overdue=20)
    fee_l3 = _fee(db, school, p1, days_overdue=45)

    summary = fee_reminders.run_fee_reminders(db, school.id, admin)
    db.commit()

    assert summary["reminded"] == 3 and summary["escalated"] == 1
    levels = {r.fee_id: r for r in db.query(models.FeeReminder).all()}
    assert levels[fee_l1.id].level == 1 and "sms" in levels[fee_l1.id].channels
    assert levels[fee_l2.id].level == 2 and levels[fee_l2.id].channels == ["notification"]
    assert levels[fee_l3.id].level == 3
    assert summary["sms_queued"] == 2  # only the students with a parent phone
    assert db.query(models.SmsMessage).count() == 2


def test_rerun_is_idempotent_and_paid_or_future_skipped():
    db = _session()
    school, admin = _school_admin(db)
    _u, profile = _student(db, school, uuid.uuid4().hex[:5])
    _fee(db, school, profile, days_overdue=5)                    # remindable
    _fee(db, school, profile, days_overdue=-3)                   # not due yet
    _fee(db, school, profile, days_overdue=10, amount=5000, paid=5000)  # fully paid

    first = fee_reminders.run_fee_reminders(db, school.id, admin)
    db.commit()
    assert first["reminded"] == 1 and first["skipped_not_due"] == 1 and first["skipped_paid"] == 1

    second = fee_reminders.run_fee_reminders(db, school.id, admin)
    db.commit()
    assert second["reminded"] == 0 and second["skipped_cooldown"] == 1


def test_level_escalation_resends_after_cooldown():
    db = _session()
    school, admin = _school_admin(db)
    _u, profile = _student(db, school, uuid.uuid4().hex[:5])
    fee = _fee(db, school, profile, days_overdue=45)  # already level 3 territory
    # Simulate an old level-1 reminder sent long ago.
    db.add(models.FeeReminder(fee_id=fee.id, school_id=school.id, student_id=profile.id, level=1, outstanding_amount=10000, channels=["notification"], created_at=datetime.now(timezone.utc) - timedelta(days=20)))
    db.commit()

    summary = fee_reminders.run_fee_reminders(db, school.id, admin)
    db.commit()
    assert summary["reminded"] == 1
    latest = db.query(models.FeeReminder).order_by(models.FeeReminder.id.desc()).first()
    assert latest.level == 3


def test_tenant_scope_and_endpoint_rbac():
    db = _session()
    school_a, admin_a = _school_admin(db)
    school_b, _admin_b = _school_admin(db)
    _u, profile_b = _student(db, school_b, uuid.uuid4().hex[:5])
    _fee(db, school_b, profile_b, days_overdue=10)

    # Running for school A must not touch school B's fees.
    summary = fee_reminders.run_fee_reminders(db, school_a.id, admin_a)
    db.commit()
    assert summary["scanned"] == 0
    assert db.query(models.FeeReminder).count() == 0

    # Endpoint RBAC: a teacher cannot trigger the run.
    teacher = models.User(email=f"t_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school_a.id, is_active=True)
    db.add(teacher); db.commit()
    try:
        automations.run_fee_reminders(level2_days=15, level3_days=30, cooldown_days=3, school_id=None, db=db, current_user=teacher)
        assert False
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403

    # History endpoint works for the admin.
    rows = automations.fee_reminder_history(limit=50, school_id=None, db=db, current_user=admin_a)
    assert rows == []
