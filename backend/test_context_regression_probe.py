"""Probe: does creating a second school break the first school's write context?

Raised by the deep attendance suite: `_mark()` on school A starts answering
403 "Eleve hors du contexte d'inscription actif" from the moment the
`neighbour` fixture creates school B. If that reproduces outside the test
fixtures it is a multi-tenant context defect, not a test artifact — recording
attendance would break for every existing school as soon as a new school is
registered on the platform.
"""

import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
PASSWORD = "SecurePass123!"


def _build(tag: str) -> dict:
    email = f"ctx_{tag}@test.com"
    client.post("/auth/register/school", json={
        "school": {"name": f"E {tag}", "domain_prefix": f"ctx{tag}",
                   "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin",
                  "password": PASSWORD}})
    token = client.post("/auth/token",
                        data={"username": email, "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/education/academic-years",
                json={"name": f"Y{tag}", "start_date": "2026-09-01T00:00:00",
                      "end_date": "2027-06-30T00:00:00", "is_current": True}, headers=headers)
    klass = client.post("/education/classes",
                        json={"name": f"5e{tag}", "level": "5e", "main_teacher_id": None},
                        headers=headers).json()
    subject = client.post("/education/subjects", json={"name": f"H{tag}"},
                          headers=headers).json()
    slot = client.post("/education/timetables",
                       json={"day_of_week": "monday", "start_time": "08:00:00",
                             "end_time": "09:00:00", "room": "A1", "class_id": klass["id"],
                             "subject_id": subject["id"], "teacher_id": None},
                       headers=headers).json()
    student = client.post("/students/", json={
        "email": f"eleve_ctx_{tag}@test.com", "password": "StudentPass123!",
        "school_domain_prefix": f"ctx{tag}", "full_name": f"Eleve {tag}", "role": "student",
        "profile": {"registration_number": f"CTX-{tag}",
                    "date_of_birth": "2012-01-01T00:00:00", "gender": "F",
                    "parent_name": "P", "parent_phone": "+2250102030405",
                    "current_class_id": klass["id"]}}, headers=headers).json()
    # `/students/` returns the ACCOUNT (User); attendance references the pupil
    # PROFILE. Sending the wrong one only appears to work while the two id
    # sequences happen to coincide (single school) — which is itself a finding.
    return {"headers": headers, "slot": slot["id"], "student": student["id"],
            "profile": (student.get("student_profile") or {}).get("id")}


def _mark(school: dict, day: int):
    return client.post("/attendance/batch", json={
        "timetable_id": school["slot"], "date": datetime(2026, 9, day).isoformat(),
        "students": [{"student_id": school["profile"], "status": "present",
                      "remarks": None}]}, headers=school["headers"])


def test_registering_a_new_school_does_not_break_an_existing_schools_attendance():
    tag = uuid.uuid4().hex[:5]
    a = _build(f"a{tag}")
    before = _mark(a, 7)
    assert before.status_code == 200, f"pre-condition failed: {before.text}"

    _build(f"b{tag}")  # a brand-new school appears on the platform

    after = _mark(a, 8)
    assert after.status_code == 200, (
        "REGRESSION DE CONTEXTE : l'ecole A ne peut plus enregistrer de presences "
        f"depuis la creation de l'ecole B -> HTTP {after.status_code} {after.text[:200]}"
    )
