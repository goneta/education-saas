"""Seconde passe d'audit — régressions et défauts trouvés à la relecture.

Four defects, three of them introduced by the remediation batches themselves:
- report card registry ids collided between students (BUG-B);
- the attendance list was unbounded AND readable by any school member (BUG-D);
- the "no visible student" scope path was never exercised end to end;
- (BUG-A, next.config build break, and BUG-C, a wrong dependency pin, are
  configuration files and are covered by the CI build rather than by pytest.)
"""

import uuid
from datetime import datetime, time, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, security
from backend.routers import attendance as attendance_router
from backend.routers import school_life
from backend.services import report_cards


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _student(db, school, name="Élève"):
    tag = uuid.uuid4().hex[:6]
    user = models.User(email=f"e_{tag}@x.com", hashed_password="x", full_name=name,
                       role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"MAT-{tag}")
    db.add(profile); db.commit()
    return user, profile


# --- BUG-B: bulletin registry identity ---------------------------------------

def test_report_card_registry_ids_never_collide():
    """`int(f"{student}{term}")` made student 1/term 23 and student 12/term 3
    share ONE registry row: the QR of one bulletin resolved to the other pupil."""
    pairs = [(1, 23), (12, 3), (123, 4), (1, 234), (7, 7), (77, 7), (7, 77)]
    ids = [report_cards.registry_source_id(student, term) for student, term in pairs]
    assert len(ids) == len(set(ids)), "two different bulletins share a registry id"
    # And the mapping stays stable for the same pair (idempotent regeneration).
    assert report_cards.registry_source_id(12, 3) == report_cards.registry_source_id(12, 3)


def test_two_students_get_two_distinct_registry_entries():
    db = _session()
    school = _school(db)
    _u1, alice = _student(db, school, "Alice")
    _u2, bob = _student(db, school, "Bob")
    term = models.Term(name="Trimestre 1")
    db.add(term); db.commit()

    class _Report:
        subjects = []
        overall_average = 12.0

    for profile in (alice, bob):
        context = report_cards.build_context(db, profile=profile, term_id=term.id, report=_Report())
        report_cards.attach_registry(db, context)
    db.commit()

    rows = db.query(models.DocumentRegistry).filter_by(source_type="report_card").all()
    assert len(rows) == 2
    assert len({row.uuid for row in rows}) == 2
    assert {row.issued_to_name for row in rows} == {"Alice", "Bob"}


# --- BUG-D: attendance list volumetrics + row-level scope --------------------

def _attendance_env():
    db = _session()
    school = _school(db)
    cls = models.Class(name="6e A", level="6EME", school_id=school.id)
    subject = models.Subject(name="Maths", code=f"M{uuid.uuid4().hex[:4]}", school_id=school.id)
    db.add_all([cls, subject]); db.flush()
    slot = models.Timetable(class_id=cls.id, subject_id=subject.id, day_of_week="monday",
                            start_time=time(8, 0), end_time=time(9, 0))
    db.add(slot); db.commit()

    app = FastAPI(); app.include_router(attendance_router.router)
    app.dependency_overrides[database.get_db] = lambda: db
    return app, db, school, slot


def _client(app, user):
    app.dependency_overrides[security.get_current_user] = lambda: user
    return TestClient(app)


def test_attendance_list_is_paginated():
    app, db, school, slot = _attendance_env()
    _user, profile = _student(db, school)
    for day in range(1, 26):
        db.add(models.Attendance(student_id=profile.id, timetable_id=slot.id,
                                 date=datetime(2026, 6, day, tzinfo=timezone.utc),
                                 status=models.AttendanceStatus.PRESENT))
    db.commit()

    admin = models.User(email=f"a_{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", full_name="A",
                        role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    client = _client(app, admin)

    assert len(client.get("/attendance/?limit=10").json()) == 10          # bounded
    assert len(client.get("/attendance/?limit=10&skip=20").json()) == 5   # paging works
    # The hard cap protects the server even from an absurd request.
    assert len(client.get("/attendance/?limit=100000").json()) == 25


def test_attendance_is_row_scoped_for_learners_and_parents():
    app, db, school, slot = _attendance_env()
    alice_user, alice = _student(db, school, "Alice")
    _bob_user, bob = _student(db, school, "Bob")
    for profile in (alice, bob):
        db.add(models.Attendance(student_id=profile.id, timetable_id=slot.id,
                                 date=datetime(2026, 6, 1, tzinfo=timezone.utc),
                                 status=models.AttendanceStatus.ABSENT))
    parent = models.User(email=f"p_{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", full_name="P",
                         role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.flush()
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=alice.id))
    db.commit()

    # A pupil sees only their own records — even when asking for a classmate's.
    alice_client = _client(app, alice_user)
    assert len(alice_client.get("/attendance/").json()) == 1
    assert alice_client.get(f"/attendance/?student_id={bob.id}").json() == []

    # A parent sees only their linked child.
    parent_client = _client(app, parent)
    assert len(parent_client.get("/attendance/").json()) == 1
    assert parent_client.get(f"/attendance/?student_id={bob.id}").json() == []


def test_user_without_any_visible_student_gets_an_empty_list_not_everything():
    """The scope path that was never exercised end to end: an empty allow-set
    must yield nothing, never the whole school."""
    app, db, school, slot = _attendance_env()
    _user, profile = _student(db, school)
    db.add(models.Attendance(student_id=profile.id, timetable_id=slot.id,
                             date=datetime(2026, 6, 1, tzinfo=timezone.utc),
                             status=models.AttendanceStatus.PRESENT))
    lonely_parent = models.User(email=f"p_{uuid.uuid4().hex[:6]}@x.com", hashed_password="x",
                                full_name="P", role=models.UserRole.PARENT,
                                school_id=school.id, is_active=True)
    db.add(lonely_parent); db.commit()

    assert _client(app, lonely_parent).get("/attendance/").json() == []

    # Same rule on the Vie scolaire modules.
    life_app = FastAPI(); life_app.include_router(school_life.router)
    life_app.dependency_overrides[database.get_db] = lambda: db
    response = _client(life_app, lonely_parent).get("/school-life/discipline")
    assert response.status_code == 200 and response.json()["total"] == 0
