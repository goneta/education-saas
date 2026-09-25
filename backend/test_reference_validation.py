"""Reference edits must preserve the values available to school forms."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.services import reference_data as refs
from backend.test_reference_data import _school, _session, _user


@pytest.fixture
def context():
    db = _session()
    school = _school(db)
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)
    root = _user(db, None, models.UserRole.SUPER_ADMIN)
    try:
        yield db, school, admin, root
    finally:
        db.close()
        db.get_bind().dispose()


def test_edit_cannot_hide_local_item_behind_global_code(context):
    db, school, admin, root = context
    refs.create_item(db, "fee_type", current_user=root, name="Tuition", code="TUITION")
    local = refs.create_item(db, "fee_type", current_user=admin, name="Lab", code="LAB")
    with pytest.raises(HTTPException) as exc:
        refs.update_item(db, local["id"], current_user=admin, data={"code": "tuition"})
    assert exc.value.status_code == 409
    assert {row["code"] for row in refs.merged_items(db, "fee_type", school.id)} == {"TUITION", "LAB"}


def test_edit_rejects_blank_name_without_mutating(context):
    db, _, admin, _ = context
    item = refs.create_item(db, "fee_type", current_user=admin, name="Lab")
    with pytest.raises(HTTPException) as exc:
        refs.update_item(db, item["id"], current_user=admin, data={"name": "   "})
    assert exc.value.status_code == 422
    assert db.get(models.ReferenceItem, item["id"]).name == "Lab"


def test_edit_rejects_duplicate_local_code(context):
    db, _, admin, _ = context
    first = refs.create_item(db, "fee_type", current_user=admin, name="First")
    second = refs.create_item(db, "fee_type", current_user=admin, name="Second")
    with pytest.raises(HTTPException) as exc:
        refs.update_item(db, second["id"], current_user=admin, data={"code": first["code"]})
    assert exc.value.status_code == 409


def test_global_creation_cannot_hide_existing_local_value(context):
    db, school, admin, root = context
    refs.create_item(db, "fee_type", current_user=admin, name="Lab")
    with pytest.raises(HTTPException) as exc:
        refs.create_item(db, "fee_type", current_user=root, name="Lab")
    assert exc.value.status_code == 409
    assert len(refs.merged_items(db, "fee_type", school.id)) == 1


def test_global_edit_cannot_hide_existing_local_value(context):
    db, _, admin, root = context
    refs.create_item(db, "fee_type", current_user=admin, name="Lab")
    item = refs.create_item(db, "fee_type", current_user=root, name="Tuition")
    with pytest.raises(HTTPException) as exc:
        refs.update_item(db, item["id"], current_user=root, data={"code": "LAB"})
    assert exc.value.status_code == 409


def test_inactive_values_still_reserve_their_code(context):
    db, _, admin, root = context
    item = refs.create_item(db, "fee_type", current_user=root, name="Lab")
    refs.update_item(db, item["id"], current_user=root, data={"is_active": False})
    with pytest.raises(HTTPException) as exc:
        refs.create_item(db, "fee_type", current_user=admin, name="Lab")
    assert exc.value.status_code == 409


def test_other_schools_can_reuse_local_codes(context):
    db, _, admin, _ = context
    other = _user(db, _school(db), models.UserRole.SCHOOL_ADMIN)
    refs.create_item(db, "fee_type", current_user=admin, name="Lab")
    item = refs.create_item(db, "fee_type", current_user=other, name="Lab")
    assert item["school_id"] == other.school_id


def test_edit_cannot_reuse_legacy_school_level_code(context):
    db, _, admin, _ = context
    db.add(models.SchoolLevel(code="CP1", name="CP1", is_active=True))
    item = refs.create_item(db, "school_level", current_user=admin, name="Local")
    with pytest.raises(HTTPException) as exc:
        refs.update_item(db, item["id"], current_user=admin, data={"code": "CP1"})
    assert exc.value.status_code == 409


def test_normalized_unchanged_code_is_valid(context):
    db, _, admin, _ = context
    item = refs.create_item(db, "fee_type", current_user=admin, name="Lab")
    updated = refs.update_item(db, item["id"], current_user=admin, data={"code": " lab ", "name": " Laboratory "})
    assert updated["code"] == "LAB"
    assert updated["name"] == "Laboratory"


def test_rejected_update_preserves_other_fields(context):
    db, _, admin, root = context
    refs.create_item(db, "fee_type", current_user=root, name="Tuition")
    item = refs.create_item(db, "fee_type", current_user=admin, name="Lab")
    with pytest.raises(HTTPException):
        refs.update_item(db, item["id"], current_user=admin, data={"name": "Changed", "code": "TUITION"})
    db.flush()
    assert db.get(models.ReferenceItem, item["id"]).name == "Lab"


@pytest.mark.parametrize("code", ["", "  ", 123, [], {}])
def test_creation_rejects_invalid_codes(context, code):
    db, _, admin, _ = context
    with pytest.raises(HTTPException) as exc:
        refs.create_item(db, "fee_type", current_user=admin, name="Lab", code=code)
    assert exc.value.status_code == 422


@pytest.mark.parametrize("payload", [
    {"name": "Lab", "sort_order": "invalid"},
    {"name": "Lab", "code": {}},
    {"name": "Lab", "scope": "typo"},
    {"name": "Lab", "school_id": -1},
])
def test_invalid_create_payload_returns_422(context, payload):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend import database, security
    from backend.routers.reference_data import router

    db, _, admin, _ = context
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[database.get_db] = lambda: db
    app.dependency_overrides[security.get_current_user] = lambda: admin
    with TestClient(app) as client:
        response = client.post("/reference-data/fee_type", json=payload)
    assert response.status_code == 422
    assert db.query(models.ReferenceItem).count() == 0
