"""Regression tests for production 500s caused by overly-strict response_model
validation choking on real stored data. These go through the HTTP stack with
TestClient so FastAPI's response serialization actually runs (direct-call unit
tests bypass it, which is why these bugs reached production).
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend import database, models, security


@pytest.fixture()
def client_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    import backend.main as main_module
    main_module.app.dependency_overrides[database.get_db] = override_db
    client = TestClient(main_module.app, raise_server_exceptions=False)
    db = Session()
    yield client, db
    db.close()
    main_module.app.dependency_overrides.clear()


def _context(db):
    org = models.Organization(name="Org", is_active=True)
    db.add(org); db.flush()
    school = models.School(name="Sch", domain_prefix=f"s{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL, organization_id=org.id, is_active=True)
    db.add(school); db.flush()
    sm = models.SchoolModel(code=f"m{uuid.uuid4().hex[:4]}", name="Mod", is_active=True)
    db.add(sm); db.flush()
    assign = models.SchoolModelAssignment(school_id=school.id, school_model_id=sm.id, is_active=True)
    db.add(assign); db.flush()
    year = models.AcademicYear(name="2026-2027", school_id=school.id, school_model_assignment_id=assign.id, is_current=True)
    db.add(year); db.flush()
    admin = models.User(email="admin@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SUPER_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.flush()
    db.add(models.UserPreference(user_id=admin.id, active_organization_id=org.id, active_school_id=school.id, active_school_model_assignment_id=assign.id, active_academic_year_id=year.id))
    db.commit()
    return org, school, assign, admin


def _auth(admin):
    return {"Authorization": f"Bearer {security.create_access_token({'sub': admin.email})}"}


def test_teachers_list_tolerates_reserved_domain_email(client_db):
    client, db = client_db
    _org, school, assign, admin = _context(db)
    # A teacher whose stored email strict EmailStr rejects (reserved domain).
    tu = models.User(email="prof@carine.local", hashed_password="x", full_name="Prof", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(tu); db.flush()
    db.add(models.TeacherAssignment(user_id=tu.id, school_id=school.id, school_model_assignment_id=assign.id, is_active=True))
    db.commit()
    resp = client.get("/teachers", headers=_auth(admin))
    assert resp.status_code == 200, resp.text
    assert resp.json()[0]["email"] == "prof@carine.local"


def test_auth_me_tolerates_bad_email(client_db):
    client, db = client_db
    school = models.School(name="S", domain_prefix=f"s{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL, is_active=True)
    db.add(school); db.flush()
    admin = models.User(email="boss@carine.local", hashed_password="x", full_name="Boss", role=models.UserRole.SUPER_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    resp = client.get("/auth/me", headers=_auth(admin))
    assert resp.status_code == 200, resp.text


def test_cart_tolerates_non_dict_metadata(client_db):
    client, db = client_db
    school = models.School(name="S", domain_prefix=f"s{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL, is_active=True)
    db.add(school); db.flush()
    admin = models.User(email="admin@example.com", hashed_password="x", full_name="A", role=models.UserRole.SUPER_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.flush()
    db.add(models.CartItem(user_id=admin.id, item_type="ai_credits", title="P", quantity=1, unit_amount=1000, currency="FCFA", provider_scope="platform", metadata_json=["legacy", "list"]))
    db.add(models.CartItem(user_id=admin.id, item_type="ai_credits", title="Q", quantity=2, unit_amount=500, currency="FCFA", provider_scope="platform", metadata_json="a-string"))
    db.commit()
    resp = client.get("/account/cart", headers=_auth(admin))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["items"]) == 2
    assert all(item["metadata_json"] is None for item in body["items"])  # non-dict normalized
