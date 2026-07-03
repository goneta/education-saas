import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import automations
from backend.services import rentree


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


def _levels(db):
    codes = []
    for order, code in enumerate(["6EME", "5EME", "4EME"]):
        tag = uuid.uuid4().hex[:4]
        unique = f"{code}_{tag}"
        db.add(models.SchoolLevel(code=unique, name=code, category="college", sort_order=order, is_active=True))
        codes.append(unique)
    db.commit()
    return codes


def _class(db, school, name, level):
    cls = models.Class(name=name, level=level, school_id=school.id)
    db.add(cls); db.commit()
    return cls


def _student(db, school, cls):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}", current_class_id=cls.id, status=models.StudentStatus.ASSIGNED)
    db.add(profile); db.commit()
    return profile


def _year(db, school, name="2025-2026", current=True):
    year = models.AcademicYear(name=name, school_id=school.id, is_current=current,
                               start_date=datetime.utcnow() - timedelta(days=300), end_date=datetime.utcnow())
    db.add(year); db.commit()
    return year


def test_preview_counts_promotions_and_leavers():
    db = _session()
    school, _admin = _school_admin(db)
    l6, l5, l4 = _levels(db)
    year = _year(db, school)
    c6 = _class(db, school, "6A", l6)
    _class(db, school, "5A", l5)
    c4 = _class(db, school, "4A", l4)  # terminal level of this school
    for _ in range(3):
        _student(db, school, c6)
    _student(db, school, c4)
    db.add(models.FeeSchedule(name="Scolarité", amount=100000, academic_year_id=year.id, level=l6, school_id=school.id))
    db.commit()

    plan = rentree.plan_rentree(db, school.id)
    assert plan["current_year"] == "2025-2026"
    assert plan["promotions"] == [{"level_from": l6, "level_to": l5, "students": 3}]
    assert plan["leavers"] == 1  # the 4EME student has no next class here
    assert plan["fee_schedules_to_clone"] == 1


def test_run_promotes_archives_and_clones():
    db = _session()
    school, admin = _school_admin(db)
    l6, l5, l4 = _levels(db)
    year = _year(db, school)
    c6 = _class(db, school, "6A", l6)
    c5a = _class(db, school, "5A", l5)
    c5b = _class(db, school, "5B", l5)
    c4 = _class(db, school, "4A", l4)
    promoted_profiles = [_student(db, school, c6) for _ in range(4)]
    leaver = _student(db, school, c4)
    db.add(models.FeeSchedule(name="Scolarité", amount=100000, academic_year_id=year.id, level=l6, school_id=school.id))
    db.commit()

    summary = rentree.run_rentree(db, school.id, admin, new_year_name="2026-2027",
                                  start_date=datetime(2026, 9, 1), end_date=datetime(2027, 6, 30))
    db.commit()

    assert summary["promoted"] == 4 and summary["archived"] == 1 and summary["fee_schedules_cloned"] == 1

    # New year is current, old one no longer is.
    current = db.query(models.AcademicYear).filter(models.AcademicYear.school_id == school.id, models.AcademicYear.is_current == True).all()  # noqa: E712
    assert len(current) == 1 and current[0].name == "2026-2027"

    # Promotions balanced across the two 5EME classes (2 + 2).
    for profile in promoted_profiles:
        db.refresh(profile)
        assert profile.current_class_id in (c5a.id, c5b.id)
        assert profile.previous_level == l6 and profile.previous_class == "6A"
    counts = [db.query(models.StudentProfile).filter(models.StudentProfile.current_class_id == cid).count() for cid in (c5a.id, c5b.id)]
    assert sorted(counts) == [2, 2]

    # Leaver archived: class cleared, history kept, account still active.
    db.refresh(leaver)
    assert leaver.current_class_id is None and leaver.status == models.StudentStatus.UNASSIGNED
    assert leaver.previous_level == l4
    assert leaver.user.is_active is True

    # Fee schedule cloned onto the new year; old one demoted.
    new_year = db.query(models.AcademicYear).filter(models.AcademicYear.name == "2026-2027").one()
    clones = db.query(models.FeeSchedule).filter(models.FeeSchedule.academic_year_id == new_year.id).all()
    assert len(clones) == 1 and clones[0].is_current is True and clones[0].amount == 100000
    old = db.query(models.FeeSchedule).filter(models.FeeSchedule.academic_year_id == year.id).one()
    assert old.is_current is False

    # Completion notification recorded.
    assert db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "rentree.completed").count() == 1


def test_run_refuses_duplicate_year_and_bad_dates():
    db = _session()
    school, admin = _school_admin(db)
    _year(db, school, name="2026-2027", current=True)

    try:
        rentree.run_rentree(db, school.id, admin, new_year_name="2026-2027",
                            start_date=datetime(2026, 9, 1), end_date=datetime(2027, 6, 30))
        assert False
    except HTTPException as exc:
        assert exc.status_code == 409

    try:
        rentree.run_rentree(db, school.id, admin, new_year_name="2027-2028",
                            start_date=datetime(2027, 9, 1), end_date=datetime(2027, 9, 1))
        assert False
    except HTTPException as exc:
        assert exc.status_code == 422


def test_endpoint_rbac_accountant_denied():
    db = _session()
    school, _admin = _school_admin(db)
    accountant = models.User(email=f"acc_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="Acc", role=models.UserRole.ACCOUNTANT, school_id=school.id, is_active=True)
    db.add(accountant); db.commit()

    try:
        automations.rentree_preview(school_id=None, db=db, current_user=accountant)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403

    payload = schemas.RentreeRunRequest(new_year_name="2026-2027", start_date=datetime(2026, 9, 1), end_date=datetime(2027, 6, 30))
    try:
        automations.rentree_run(payload=payload, school_id=None, db=db, current_user=accountant)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403
