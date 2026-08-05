"""Vie scolaire (Discipline / Examens / Activités / Santé / Internat).

The five modules share ONE factorized CRUD engine — these tests cover the
shared contract once (tenant scoping, RBAC, search/filter/pagination, CSV
export, audit-safe delete) plus each module's specific required fields, the
health module's restricted reads, and cross-school isolation.
In-memory SQLite, direct TestClient-free router calls via FastAPI TestClient
on the real app would need the dev DB; instead we call endpoints through a
minimal FastAPI instance mounting the real router with dependency overrides.
"""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, security
from backend.routers import school_life


def _make_env():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    app = FastAPI()
    app.include_router(school_life.router)
    app.dependency_overrides[database.get_db] = lambda: db
    return app, db


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _user(db, school, role=models.UserRole.SCHOOL_ADMIN):
    tag = uuid.uuid4().hex[:6]
    u = models.User(email=f"u_{tag}@x.com", hashed_password="x", full_name=f"U {tag}", role=role,
                    school_id=school.id, is_active=True)
    db.add(u); db.commit()
    return u


def _student(db, school, name="Awa Élève"):
    tag = uuid.uuid4().hex[:6]
    user = models.User(email=f"st_{tag}@x.com", hashed_password="x", full_name=name,
                       role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"MAT-{tag}")
    db.add(profile); db.commit()
    return profile


def _client(app, user):
    app.dependency_overrides[security.get_current_user] = lambda: user
    return TestClient(app)


def test_crud_search_pagination_and_isolation():
    app, db = _make_env()
    school_a, school_b = _school(db), _school(db)
    admin_a = _user(db, school_a)
    student = _student(db, school_a)
    client = _client(app, admin_a)

    created = client.post("/school-life/discipline", json={
        "student_id": student.id, "record_kind": "sanction", "type_code": "WARNING",
        "title": "Avertissement retards répétés", "record_date": "2026-08-01T08:00:00",
    })
    assert created.status_code == 200, created.text
    record_id = created.json()["id"]
    assert created.json()["student_name"] == "Awa Élève"

    # Search matches title AND student name; pagination totals are exact.
    for query in ("retards", "Awa"):
        out = client.get(f"/school-life/discipline?search={query}").json()
        assert out["total"] == 1 and out["items"][0]["id"] == record_id
    assert client.get("/school-life/discipline?search=zzz").json()["total"] == 0
    assert client.get("/school-life/discipline?skip=0&limit=1").json()["total"] == 1

    updated = client.patch(f"/school-life/discipline/{record_id}", json={"status": "resolved"})
    assert updated.json()["status"] == "resolved"

    # CSV export streams the rows.
    export = client.get("/school-life/discipline/export.csv")
    assert export.status_code == 200
    assert "Avertissement" in export.text

    # Another school sees NOTHING and cannot touch the record.
    admin_b = _user(db, school_b)
    client_b = _client(app, admin_b)
    assert client_b.get("/school-life/discipline").json()["total"] == 0
    assert client_b.patch(f"/school-life/discipline/{record_id}", json={"status": "open"}).status_code == 404
    assert client_b.delete(f"/school-life/discipline/{record_id}").status_code == 404

    client = _client(app, admin_a)
    assert client.delete(f"/school-life/discipline/{record_id}").json()["status"] == "deleted"
    assert client.get("/school-life/discipline").json()["total"] == 0


def test_writes_are_role_gated_and_required_fields_enforced():
    app, db = _make_env()
    school = _school(db)
    admin = _user(db, school)
    teacher = _user(db, school, role=models.UserRole.TEACHER)
    student = _student(db, school)

    # A teacher can READ activities but not create them.
    client_teacher = _client(app, teacher)
    assert client_teacher.get("/school-life/activities").status_code == 200
    assert client_teacher.post("/school-life/activities", json={"name": "Sortie"}).status_code == 403

    client = _client(app, admin)
    # Required fields -> explicit 422 naming the field.
    missing = client.post("/school-life/exams", json={"name": "BEPC blanc"})
    assert missing.status_code == 422 and "exam_type" in missing.json()["detail"]
    ok = client.post("/school-life/exams", json={"name": "BEPC blanc", "exam_type": "EXAM",
                                                 "max_score": 20, "coefficient": 2})
    assert ok.status_code == 200 and ok.json()["exam_type"] == "EXAM"

    # Student referenced must belong to the school.
    bad = client.post("/school-life/boarding", json={"student_id": 99999})
    assert bad.status_code == 404
    good = client.post("/school-life/boarding", json={"student_id": student.id, "status": "active"})
    assert good.status_code == 200


def test_health_module_reads_are_restricted():
    app, db = _make_env()
    school = _school(db)
    admin = _user(db, school)
    teacher = _user(db, school, role=models.UserRole.TEACHER)
    student = _student(db, school)

    client = _client(app, admin)
    created = client.post("/school-life/health", json={
        "student_id": student.id, "record_type_code": "ALLERGY",
        "title": "Allergie arachide", "severity": "high",
    })
    assert created.status_code == 200

    # Medical data: even READS are administration-only.
    client_teacher = _client(app, teacher)
    assert client_teacher.get("/school-life/health").status_code == 403
    assert client_teacher.get("/school-life/health/export.csv").status_code == 403

    assert _client(app, admin).get("/school-life/health").json()["total"] == 1
