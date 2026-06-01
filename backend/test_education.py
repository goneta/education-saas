import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _admin():
    unique_id = uuid.uuid4().hex[:8]
    domain = f"school_{unique_id}"
    email = f"admin_{unique_id}@test.com"
    password = "securepassword123"
    client.post("/auth/register/school", json={
        "school": {"name": f"Test School {unique_id}", "domain_prefix": domain, "school_type": "general", "address": "123 Education St"},
        "owner": {"email": email, "full_name": "Test Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_education_flow():
    headers = _admin()

    created_class = client.post("/education/classes", json={"name": "6eme A", "level": "6eme"}, headers=headers)
    assert created_class.status_code == 200
    class_id = created_class.json()["id"]

    created_subject = client.post("/education/subjects", json={"name": "Mathematics", "code": "MATH", "coefficient": 5}, headers=headers)
    assert created_subject.status_code == 200
    subject_id = created_subject.json()["id"]

    timetable_payload = {
        "day_of_week": "monday",
        "start_time": "08:00:00",
        "end_time": "10:00:00",
        "room": "101",
        "class_id": class_id,
        "subject_id": subject_id,
    }
    created_timetable = client.post("/education/timetables", json=timetable_payload, headers=headers)
    assert created_timetable.status_code == 200
    timetable_id = created_timetable.json()["id"]

    listed = client.get(f"/education/timetables?class_id={class_id}", headers=headers)
    assert listed.status_code == 200
    assert any(row["id"] == timetable_id for row in listed.json())

    assert client.delete(f"/education/timetables/{timetable_id}", headers=headers).status_code == 204
    assert client.delete(f"/education/classes/{class_id}", headers=headers).status_code in {200, 204}
    assert client.delete(f"/education/subjects/{subject_id}", headers=headers).status_code in {200, 204}
