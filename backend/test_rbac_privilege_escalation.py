import uuid

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _school_admin():
    uid = uuid.uuid4().hex[:8]
    email = f"admin_{uid}@test.com"
    password = "SecurePass123!"
    client.post("/auth/register/school", json={
        "school": {"name": f"Esc {uid}", "domain_prefix": f"esc_{uid}", "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, uid


def test_school_admin_cannot_assign_privileged_role_keys():
    headers, uid = _school_admin()
    created = client.post("/system/users", headers=headers, json={
        "email": f"u_{uid}@test.com", "full_name": "User", "password": "SecurePass123!",
        "role": "teacher", "role_keys": ["teacher"],
    })
    assert created.status_code == 200, created.text
    user_id = created.json()["id"]

    for privileged in ("super_admin", "school_admin", "admin"):
        res = client.put(f"/system/users/{user_id}/roles", headers=headers, json={"role_keys": [privileged]})
        assert res.status_code == 403, f"{privileged} should be forbidden, got {res.status_code}"

    # A normal role key still works.
    ok = client.put(f"/system/users/{user_id}/roles", headers=headers, json={"role_keys": ["educator"]})
    assert ok.status_code == 200, ok.text


def test_school_admin_cannot_create_or_promote_to_wildcard_admin_roles():
    headers, uid = _school_admin()
    # Creating any wildcard admin primary role (admin/school_admin/super_admin) is forbidden.
    for role in ("admin", "school_admin", "super_admin"):
        res = client.post("/system/users", headers=headers, json={
            "email": f"new_{role}_{uid}@test.com", "full_name": "X", "password": "SecurePass123!",
            "role": role, "role_keys": [],
        })
        assert res.status_code == 403, f"creating {role} should be forbidden, got {res.status_code}: {res.text}"

    # Promoting an existing user to admin is forbidden too.
    teacher = client.post("/system/users", headers=headers, json={
        "email": f"t_{uid}@test.com", "full_name": "T", "password": "SecurePass123!",
        "role": "teacher", "role_keys": ["teacher"],
    }).json()
    promote = client.put(f"/system/users/{teacher['id']}", headers=headers, json={"role": "admin"})
    assert promote.status_code == 403
