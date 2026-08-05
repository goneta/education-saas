"""Lot 1 — audit PRIV-01 / PRIV-02 / SEC-07 / SEC-08 : confidentialité intra-établissement.

Inter-school isolation was already solid; these tests cover the row-level rule
INSIDE a school: a learner sees only their own records, a parent only their
linked children's, staff the whole school.
"""

import uuid

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, security
from backend.routers import school_life
from backend.services import access_scope, employment


def _env():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    app = FastAPI()
    app.include_router(school_life.router)
    app.dependency_overrides[database.get_db] = lambda: db
    return app, db


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _user(db, school, role):
    tag = uuid.uuid4().hex[:6]
    u = models.User(email=f"u_{tag}@x.com", hashed_password="x", full_name=f"U {tag}",
                    role=role, school_id=school.id, is_active=True)
    db.add(u); db.commit()
    return u


def _student(db, school, name="Élève"):
    user = _user(db, school, models.UserRole.STUDENT)
    user.full_name = name
    profile = models.StudentProfile(user_id=user.id, registration_number=f"MAT-{uuid.uuid4().hex[:6]}")
    db.add(profile); db.commit()
    return user, profile


def _client(app, user):
    app.dependency_overrides[security.get_current_user] = lambda: user
    return TestClient(app)


def test_learner_and_parent_only_see_their_own_discipline_records():
    """PRIV-01: the critical finding — a student could read every classmate's
    disciplinary record by walking identifiers."""
    app, db = _env()
    school = _school(db)
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)
    alice_user, alice = _student(db, school, "Alice")
    bob_user, bob = _student(db, school, "Bob")

    parent = _user(db, school, models.UserRole.PARENT)
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=alice.id)); db.commit()

    staff_client = _client(app, admin)
    for profile, title in ((alice.id, "Avertissement Alice"), (bob.id, "Avertissement Bob")):
        created = staff_client.post("/school-life/discipline", json={
            "student_id": profile, "record_kind": "sanction", "title": title})
        assert created.status_code == 200, created.text
    bob_record_id = staff_client.get("/school-life/discipline?search=Bob").json()["items"][0]["id"]

    # Staff: full school view.
    assert staff_client.get("/school-life/discipline").json()["total"] == 2

    # Learner: only their own row, and Bob's record is not even fetchable by id.
    alice_client = _client(app, alice_user)
    listed = alice_client.get("/school-life/discipline").json()
    assert listed["total"] == 1 and listed["items"][0]["student_name"] == "Alice"
    assert alice_client.get(f"/school-life/discipline/{bob_record_id}").status_code == 404
    # Filtering by another student's id cannot widen the scope either.
    assert alice_client.get(f"/school-life/discipline?student_id={bob.id}").json()["total"] == 0
    # Neither can the CSV export.
    assert "Bob" not in alice_client.get("/school-life/discipline/export.csv").text

    # Parent: only the linked child.
    parent_client = _client(app, parent)
    parent_listed = parent_client.get("/school-life/discipline").json()
    assert parent_listed["total"] == 1 and parent_listed["items"][0]["student_name"] == "Alice"
    assert parent_client.get(f"/school-life/discipline/{bob_record_id}").status_code == 404


def test_boarding_is_row_scoped_and_school_wide_modules_stay_open():
    app, db = _env()
    school = _school(db)
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)
    alice_user, alice = _student(db, school, "Alice")
    _bob_user, bob = _student(db, school, "Bob")

    staff = _client(app, admin)
    staff.post("/school-life/boarding", json={"student_id": alice.id, "status": "active"})
    staff.post("/school-life/boarding", json={"student_id": bob.id, "status": "active"})
    staff.post("/school-life/exams", json={"name": "BEPC blanc", "exam_type": "EXAM"})
    staff.post("/school-life/activities", json={"name": "Sortie musée"})

    alice_client = _client(app, alice_user)
    assert alice_client.get("/school-life/boarding").json()["total"] == 1  # personal data: scoped
    # Exam calendar and activity programme carry no personal data: still visible.
    assert alice_client.get("/school-life/exams").json()["total"] == 1
    assert alice_client.get("/school-life/activities").json()["total"] == 1
    # ... but a learner still cannot write.
    assert alice_client.post("/school-life/activities", json={"name": "Fake"}).status_code == 403


def test_health_records_remain_administration_only():
    app, db = _env()
    school = _school(db)
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)
    alice_user, alice = _student(db, school, "Alice")
    _client(app, admin).post("/school-life/health", json={"student_id": alice.id, "title": "Allergie"})

    # Even the student concerned does not get the medical module (unchanged rule).
    assert _client(app, alice_user).get("/school-life/health").status_code == 403
    assert _client(app, admin).get("/school-life/health").json()["total"] == 1


def test_visible_student_ids_rules():
    """PRIV-02: the shared resolver used by every module."""
    _app, db = _env()
    school = _school(db)
    teacher = _user(db, school, models.UserRole.TEACHER)
    alice_user, alice = _student(db, school, "Alice")
    _bob_user, bob = _student(db, school, "Bob")
    parent = _user(db, school, models.UserRole.PARENT)
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=alice.id)); db.commit()

    assert access_scope.visible_student_ids(db, teacher) is None          # staff: unrestricted
    assert access_scope.visible_student_ids(db, alice_user) == {alice.id}
    assert access_scope.visible_student_ids(db, parent) == {alice.id}
    assert access_scope.can_view_student(db, alice_user, bob.id) is False
    assert access_scope.can_view_student(db, parent, bob.id) is False
    assert access_scope.can_view_student(db, teacher, bob.id) is True

    # A parent with no link, or an unrelated role, sees nothing — never everything.
    lonely_parent = _user(db, school, models.UserRole.PARENT)
    assert access_scope.visible_student_ids(db, lonely_parent) == set()


def test_cv_photo_requires_full_publication_optin():
    """SEC-07: `share_enabled` alone no longer exposes a student's photo."""
    _app, db = _env()
    cv = models.StudentCV(share_enabled=True, looking_for_job=False, privacy_settings={})
    assert employment.is_publicly_listed(cv) is False           # shared by sharecode only
    cv.looking_for_job = True
    assert employment.is_publicly_listed(cv) is False           # search visibility off by default
    cv.privacy_settings = {"visible_in_sector_search": True}
    assert employment.is_publicly_listed(cv) is True            # fully opted in
    cv.share_enabled = False
    assert employment.is_publicly_listed(cv) is False
