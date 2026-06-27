import uuid

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _admin(prefix: str):
    password = "SecurePass123!"
    email = f"admin_{prefix}_{uuid.uuid4().hex[:6]}@test.com"
    domain = f"{prefix}_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register/school", json={
        "school": {"name": f"School {prefix}", "domain_prefix": domain, "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _register_teacher(headers):
    return client.post("/teachers/", headers=headers, json={
        "email": f"teacher_{uuid.uuid4().hex[:8]}@test.com",
        "password": "TeacherPass123!",
        "full_name": "Prof Multi",
        "role": "teacher",
        "profile": {"specialization": "Maths", "bio": "x"},
    }).json()


def _teacher_ids(headers):
    res = client.get("/teachers", headers=headers)
    assert res.status_code == 200
    return {row["id"] for row in res.json()}


def test_teacher_can_teach_at_two_schools_concurrently():
    school_c = _admin("teach_c")
    school_d = _admin("teach_d")
    teacher = _register_teacher(school_c)
    teacher_id = teacher["id"]

    # Initially only school C sees the teacher.
    assert teacher_id in _teacher_ids(school_c)
    assert teacher_id not in _teacher_ids(school_d)

    # School D adds the same teacher to its own context (additive, not a transfer).
    res = client.post(f"/teachers/{teacher_id}/assignments", headers=school_d, json={"specialization": "Physique"})
    assert res.status_code == 200, res.text

    # Both schools now see the teacher concurrently.
    assert teacher_id in _teacher_ids(school_c)
    assert teacher_id in _teacher_ids(school_d)

    # Listing the teacher's assignments shows two active schools.
    assignments = client.get(f"/teachers/{teacher_id}/assignments", headers=school_d).json()
    active = [a for a in assignments if a["is_active"]]
    assert len({a["school_id"] for a in active}) == 2


def test_removing_teacher_from_one_school_keeps_the_other():
    school_c = _admin("rm_c")
    school_d = _admin("rm_d")
    teacher = _register_teacher(school_c)
    teacher_id = teacher["id"]
    client.post(f"/teachers/{teacher_id}/assignments", headers=school_d, json={})

    # School D removes the teacher: only D's assignment ends, C keeps them.
    res = client.delete(f"/teachers/{teacher_id}", headers=school_d)
    assert res.status_code == 204
    assert teacher_id not in _teacher_ids(school_d)
    assert teacher_id in _teacher_ids(school_c)


def test_lookup_resolves_existing_teacher_by_email():
    school_c = _admin("lookup_c")
    school_d = _admin("lookup_d")
    teacher = _register_teacher(school_c)
    email = client.get(f"/teachers/{teacher['id']}/assignments", headers=school_c).json()  # ensure created
    assert email  # has at least one assignment
    teacher_email = None
    # Re-fetch the teacher email from school C's list.
    for row in client.get("/teachers", headers=school_c).json():
        if row["id"] == teacher["id"]:
            teacher_email = row["email"]
    res = client.get(f"/teachers/lookup?email={teacher_email}", headers=school_d)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["id"] == teacher["id"]
    assert body["already_in_school"] is False
    # Unknown email returns 404.
    assert client.get("/teachers/lookup?email=nobody@nowhere.test", headers=school_d).status_code == 404


def test_school_cannot_view_teacher_without_an_assignment():
    school_c = _admin("view_c")
    school_d = _admin("view_d")
    teacher = _register_teacher(school_c)
    teacher_id = teacher["id"]
    # D has no assignment for this teacher: detail access is denied.
    assert client.get(f"/teachers/{teacher_id}", headers=school_d).status_code == 404
    # C owns an assignment: detail access works.
    assert client.get(f"/teachers/{teacher_id}", headers=school_c).status_code == 200
