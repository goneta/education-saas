"""Twelve independent HTTP scenarios for each school-life module."""

import pytest

from backend import security
from backend.test_school_life import _make_env, _school, _user, _student, _client


@pytest.fixture(params=["discipline", "exams", "activities", "health", "boarding"])
def env(request):
    app, db = _make_env()
    school = _school(db)
    admin = _user(db, school)
    other = _user(db, _school(db))
    student = _student(db, school)
    payloads = {
        "discipline": {"student_id": student.id, "record_kind": "sanction", "title": "Unique record"},
        "exams": {"name": "Unique record", "exam_type": "EXAM"},
        "activities": {"name": "Unique record"},
        "health": {"student_id": student.id, "title": "Unique record"},
        "boarding": {"student_id": student.id, "notes": "Unique record"},
    }
    client = _client(app, admin)
    path = f"/school-life/{request.param}"
    payload = payloads[request.param]
    created = client.post(path, json=payload)
    assert created.status_code == 200, created.text
    try:
        yield app, db, client, path, payload, created.json(), other, student.user
    finally:
        client.close()
        db.close()
        db.get_bind().dispose()


def test_detail_roundtrip(env):
    _, _, client, path, payload, row, _, _ = env
    response = client.get(f"{path}/{row['id']}")
    assert response.status_code == 200
    assert all(response.json()[key] == value for key, value in payload.items())


def test_search_filters_records(env):
    _, _, client, path, _, _, _, _ = env
    assert client.get(path, params={"search": "Unique"}).json()["total"] == 1
    assert client.get(path, params={"search": "absent-value"}).json()["items"] == []


def test_pagination_preserves_total(env):
    _, _, client, path, payload, first, _, _ = env
    second = client.post(path, json=payload).json()
    page = client.get(path, params={"skip": 1, "limit": 1}).json()
    assert page["total"] == 2
    assert [row["id"] for row in page["items"]] == [first["id"]]
    assert second["id"] != first["id"]


def test_update_persists(env):
    _, _, client, path, _, row, _, _ = env
    url = f"{path}/{row['id']}"
    assert client.patch(url, json={"status": "closed"}).status_code == 200
    assert client.get(url).json()["status"] == "closed"
    assert client.get(path, params={"status": "closed"}).json()["total"] == 1


def test_delete_removes_record(env):
    _, _, client, path, _, row, _, _ = env
    url = f"{path}/{row['id']}"
    assert client.delete(url).status_code == 200
    assert client.get(url).status_code == 404
    assert client.get(path).json()["total"] == 0


def test_cross_school_list_and_export_hide_record(env):
    app, _, client, path, _, _, other, _ = env
    app.dependency_overrides[security.get_current_user] = lambda: other
    assert client.get(path).json()["items"] == []
    export = client.get(f"{path}/export.csv")
    assert export.status_code == 200
    assert "Unique record" not in export.text


def test_cross_school_detail_is_denied(env):
    app, _, client, path, _, row, other, _ = env
    app.dependency_overrides[security.get_current_user] = lambda: other
    assert client.get(f"{path}/{row['id']}").status_code == 404


def test_cross_school_update_is_denied(env):
    app, _, client, path, _, row, other, _ = env
    app.dependency_overrides[security.get_current_user] = lambda: other
    assert client.patch(f"{path}/{row['id']}", json={"status": "closed"}).status_code == 404


def test_cross_school_delete_is_denied(env):
    app, _, client, path, _, row, other, _ = env
    app.dependency_overrides[security.get_current_user] = lambda: other
    assert client.delete(f"{path}/{row['id']}").status_code == 404


def test_student_cannot_create(env):
    app, _, client, path, payload, _, _, student = env
    app.dependency_overrides[security.get_current_user] = lambda: student
    assert client.post(path, json=payload).status_code == 403


def test_missing_required_field_is_rejected(env):
    _, _, client, path, _, _, _, _ = env
    assert client.post(path, json={}).status_code == 422


def test_patch_cannot_clear_required_field(env):
    _, _, client, path, payload, row, _, _ = env
    field = "student_id" if "student_id" in payload else "name"
    url = f"{path}/{row['id']}"
    response = client.patch(url, json={field: None})
    assert response.status_code == 422, response.text
    assert client.get(url).json()[field] == payload[field]
