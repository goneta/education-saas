import datetime
import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _school(prefix: str):
    unique = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique}@test.com"
    password = "SecurePass123!"
    created = client.post("/auth/register/school", json={
        "school": {
            "name": f"Ecole {prefix} {unique}",
            "domain_prefix": f"{prefix}_{unique}",
            "school_type": "primary",
            "address": "Abidjan",
        },
        "owner": {
            "email": email,
            "full_name": f"Admin {prefix}",
            "role": "school_admin",
            "password": password,
        },
    })
    assert created.status_code == 200, created.text
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    template = client.post(
        f"/system/schools/{created.json()['id']}/apply-template",
        headers=headers,
        json={"template": "primary"},
    )
    assert template.status_code == 200, template.text
    return created.json(), headers


def test_unique_student_transfer_finance_isolation_and_year_lock():
    school_a, headers_a = _school("lifecycle_a")
    school_b, headers_b = _school("lifecycle_b")
    unique = uuid.uuid4().hex[:8]
    student_response = client.post("/students", headers=headers_a, json={
        "email": f"student_lifecycle_{unique}@test.com",
        "password": "StudentPass123!",
        "full_name": "Awa Parcours",
        "role": "student",
        "school_id": school_a["id"],
        "profile": {
            "registration_number": f"LIFE-{unique}",
            "date_of_birth": datetime.datetime(2011, 3, 4).isoformat(),
            "gender": "F",
            "parent_name": "Parent Awa",
            "parent_phone": "+2250102030405",
            "parent_phone_country_code": "CI",
        },
    })
    assert student_response.status_code == 200, student_response.text
    student = student_response.json()

    journey_a = client.get(f"/student-lifecycle/students/{student['id']}", headers=headers_a)
    assert journey_a.status_code == 200, journey_a.text
    journey = journey_a.json()
    assert len(journey["enrollments"]) == 1
    global_profile_id = journey["id"]
    source_enrollment_id = journey["enrollments"][0]["id"]

    options_b = client.get("/context/options", headers=headers_b).json()
    assignment_b = options_b["assignments"][0]
    year_b = next(
        row for row in options_b["academic_years"]
        if row["school_model_assignment_id"] == assignment_b["id"]
    )
    requested = client.post("/student-lifecycle/transfers", headers=headers_a, json={
        "student_global_profile_id": global_profile_id,
        "from_enrollment_id": source_enrollment_id,
        "to_school_model_assignment_id": assignment_b["id"],
        "to_academic_year_id": year_b["id"],
        "academic_data_access_level": "full_history",
    })
    assert requested.status_code == 200, requested.text
    transfer_id = requested.json()["id"]
    assert client.post(
        f"/student-lifecycle/transfers/{transfer_id}/decision",
        headers=headers_b,
        json={"decision": "approved"},
    ).status_code == 200
    completed = client.post(
        f"/student-lifecycle/transfers/{transfer_id}/decision",
        headers=headers_b,
        json={"decision": "completed"},
    )
    assert completed.status_code == 200, completed.text

    listed_b = client.get("/students", headers=headers_b)
    assert listed_b.status_code == 200
    assert [row["id"] for row in listed_b.json()].count(student["id"]) == 1
    journey_b = client.get(f"/student-lifecycle/students/{student['id']}", headers=headers_b).json()
    assert len(journey_b["enrollments"]) == 2
    old_context = next(row for row in journey_b["enrollments"] if row["school_id"] == school_a["id"])
    assert old_context["financial"] is None
    assert old_context["read_only"] is True

    closed = client.post(
        f"/student-lifecycle/academic-years/{year_b['id']}/close",
        headers=headers_b,
        json={"school_model_assignment_id": assignment_b["id"], "confirmation": "CLOTURER"},
    )
    assert closed.status_code == 200, closed.text
    blocked = client.put(
        f"/students/{student['id']}",
        headers=headers_b,
        json={"full_name": "Modification interdite"},
    )
    assert blocked.status_code == 423, blocked.text


def test_concurrent_enrollment_detects_schedule_conflicts():
    school, headers = _school("concurrent")
    unique = uuid.uuid4().hex[:8]
    student = client.post("/students", headers=headers, json={
        "email": f"concurrent_{unique}@test.com",
        "password": "StudentPass123!",
        "full_name": "Koffi Technique",
        "role": "student",
        "school_id": school["id"],
        "profile": {
            "registration_number": f"CON-{unique}",
            "date_of_birth": datetime.datetime(2008, 7, 1).isoformat(),
            "gender": "M",
            "parent_name": "Parent Koffi",
            "parent_phone": "+2250102030405",
            "parent_phone_country_code": "CI",
        },
    }).json()
    journey = client.get(f"/student-lifecycle/students/{student['id']}", headers=headers).json()
    options = client.get("/context/options", headers=headers).json()
    primary_assignment = options["assignments"][0]
    year = next(row for row in options["academic_years"] if row["school_model_assignment_id"] == primary_assignment["id"])

    first = client.post("/student-lifecycle/enrollments", headers=headers, json={
        "student_global_profile_id": journey["id"],
        "school_model_assignment_id": primary_assignment["id"],
        "academic_year_id": year["id"],
        "enrollment_type": "module",
        "allows_concurrent_enrollment": True,
        "primary_enrollment": False,
        "days_of_week": ["monday"],
        "start_time": "18:00:00",
        "end_time": "20:00:00",
    })
    assert first.status_code == 200, first.text
    conflict = client.post("/student-lifecycle/enrollments", headers=headers, json={
        "student_global_profile_id": journey["id"],
        "school_model_assignment_id": primary_assignment["id"],
        "academic_year_id": year["id"],
        "enrollment_type": "module",
        "allows_concurrent_enrollment": True,
        "primary_enrollment": False,
        "days_of_week": ["monday"],
        "start_time": "19:00:00",
        "end_time": "21:00:00",
    })
    assert conflict.status_code == 409
