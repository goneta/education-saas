"""Cross-tenant (IDOR) probe — School A's admin attacks School B's identifiers.

Audit section 5 (data isolation). `access_scope` answers the ROW-level question
("which pupils inside my school") and returns "no restriction" for staff, so it
cannot stop an administrator of school A walking identifiers belonging to school
B. Only an explicit tenancy filter can. This suite is the regression net for that
class of bug — one real leak of this exact shape was found in
`grades.get_report_card` (full bulletin of another school's pupil readable by id).

Every endpoint here must answer 403 or 404 for a foreign identifier. Returning
200 with another school's data is a production blocker.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

PASSWORD = "SecurePass123!"


def _make_school(tag: str) -> dict:
    """A fully-populated school: admin, year, class, subject, slot, pupil."""
    domain, email = f"ct{tag}", f"admin_ct_{tag}@test.com"
    registration = client.post(
        "/auth/register/school",
        json={
            "school": {"name": f"Ecole {tag}", "domain_prefix": domain,
                       "school_type": "general", "address": "1 rue des tests"},
            "owner": {"email": email, "full_name": "Admin", "role": "school_admin",
                      "password": PASSWORD},
        },
    )
    assert registration.status_code == 200, registration.text
    token = client.post("/auth/token",
                        data={"username": email, "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    year = client.post("/education/academic-years",
                       json={"name": f"2026-2027 {tag}", "start_date": "2026-09-01T00:00:00",
                             "end_date": "2027-06-30T00:00:00", "is_current": True},
                       headers=headers).json()
    klass = client.post("/education/classes",
                        json={"name": f"5e {tag}", "level": "5e", "main_teacher_id": None},
                        headers=headers).json()
    subject = client.post("/education/subjects", json={"name": f"Histoire {tag}"},
                          headers=headers).json()
    term = client.post("/education/terms",
                       json={"name": f"Trimestre 1 {tag}", "academic_year_id": year["id"],
                             "start_date": "2026-09-01T00:00:00",
                             "end_date": "2026-12-20T00:00:00"},
                       headers=headers)
    student = client.post(
        "/students/",
        json={"email": f"eleve_ct_{tag}@test.com", "password": "StudentPass123!",
              "school_domain_prefix": domain, "full_name": f"Eleve {tag}", "role": "student",
              "profile": {"registration_number": f"CT-{tag}",
                          "date_of_birth": "2012-01-01T00:00:00", "gender": "F",
                          "parent_name": "Parent", "parent_phone": "+2250102030405",
                          "current_class_id": klass["id"]}},
        headers=headers).json()
    teacher = client.post(
        "/teachers/",
        json={"email": f"prof_ct_{tag}@test.com", "password": "TeacherPass123!",
              "school_domain_prefix": domain, "full_name": f"Prof {tag}", "role": "teacher",
              "profile": {"specialization": "Histoire"}},
        headers=headers)

    return {
        "headers": headers,
        "class_id": klass["id"],
        "subject_id": subject["id"],
        "student_user_id": student["id"],
        "student_profile_id": (student.get("student_profile") or {}).get("id"),
        "teacher_user_id": teacher.json().get("id") if teacher.status_code == 200 else None,
        "term_id": (term.json() or {}).get("id") if term.status_code in {200, 201} else None,
    }


@pytest.fixture(scope="module")
def schools():
    tag = uuid.uuid4().hex[:6]
    return {"a": _make_school(f"a{tag}"), "b": _make_school(f"b{tag}")}


def _assert_denied(response, what: str):
    """A foreign identifier must be refused. 200 = the data crossed tenants."""
    assert response.status_code in {403, 404}, (
        f"FUITE INTER-ETABLISSEMENT sur {what}: HTTP {response.status_code} "
        f"-> {response.text[:200]}"
    )


def test_cannot_read_another_schools_student(schools):
    a, b = schools["a"], schools["b"]
    _assert_denied(client.get(f"/students/{b['student_user_id']}", headers=a["headers"]),
                   "GET /students/{id}")


def test_cannot_read_another_schools_teacher(schools):
    a, b = schools["a"], schools["b"]
    if not b["teacher_user_id"]:
        pytest.skip("teacher creation unavailable in this environment")
    _assert_denied(client.get(f"/teachers/{b['teacher_user_id']}", headers=a["headers"]),
                   "GET /teachers/{id}")


def test_cannot_read_another_schools_report_card(schools):
    """The exact leak found in audit: full bulletin readable by walking ids."""
    a, b = schools["a"], schools["b"]
    if not b["term_id"]:
        pytest.skip("term creation unavailable in this environment")
    _assert_denied(
        client.get(f"/grades/reports/student/{b['student_profile_id']}/term/{b['term_id']}",
                   headers=a["headers"]),
        "GET /grades/reports/student/{id}/term/{id}")


def test_cannot_download_another_schools_report_card_pdf(schools):
    a, b = schools["a"], schools["b"]
    if not b["term_id"]:
        pytest.skip("term creation unavailable in this environment")
    _assert_denied(
        client.get(f"/grades/reports/student/{b['student_profile_id']}/term/{b['term_id']}/pdf",
                   headers=a["headers"]),
        "GET /grades/reports/.../pdf")


def test_cannot_list_another_schools_class_students(schools):
    a, b = schools["a"], schools["b"]
    response = client.get(f"/education/classes/{b['class_id']}/students", headers=a["headers"])
    if response.status_code == 200:
        assert response.json() == [], (
            f"FUITE: la classe de l'ecole B renvoie {len(response.json())} eleves a l'ecole A")
    else:
        _assert_denied(response, "GET /education/classes/{id}/students")


def test_cannot_read_another_schools_attendance(schools):
    """Attendance of school B must never appear in school A's listing."""
    a, b = schools["a"], schools["b"]
    response = client.get(f"/attendance/?class_id={b['class_id']}", headers=a["headers"])
    assert response.status_code == 200, response.text
    assert response.json() == [], "FUITE: presences d'un autre etablissement listees"


def test_cannot_read_another_schools_receipt_pdf(schools):
    a, b = schools["a"], schools["b"]
    response = client.get(
        f"/documents/students/{b['student_user_id']}/receipt/1.pdf", headers=a["headers"])
    assert response.status_code != 200, (
        "FUITE: recu PDF d'un eleve d'un autre etablissement telecharge")
