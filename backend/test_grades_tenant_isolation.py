import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _setup_school(prefix: str):
    uid = uuid.uuid4().hex[:8]
    email = f"admin_{prefix}_{uid}@test.com"
    password = "SecurePass123!"
    client.post("/auth/register/school", json={
        "school": {"name": f"School {prefix}", "domain_prefix": f"{prefix}_{uid}", "school_type": "general", "address": "x"},
        "owner": {"email": email, "full_name": "Admin", "role": "school_admin", "password": password},
    })
    headers = {"Authorization": f"Bearer {client.post('/auth/token', data={'username': email, 'password': password}).json()['access_token']}"}
    year_id = client.post("/education/academic-years", json={"name": "2024-2025", "start_date": "2024-09-01T00:00:00", "end_date": "2025-06-30T00:00:00", "is_current": True}, headers=headers).json()["id"]
    term_id = client.post("/education/terms", json={"name": "Term 1", "start_date": "2024-09-01T00:00:00", "end_date": "2024-12-31T00:00:00", "academic_year_id": year_id}, headers=headers).json()["id"]
    class_id = client.post("/education/classes", json={"name": "Class", "level": "L", "main_teacher_id": None}, headers=headers).json()["id"]
    subject_id = client.post("/education/subjects", json={"name": "Maths"}, headers=headers).json()["id"]
    assessment_id = client.post("/grades/assessments", json={
        "title": "Exam", "type": "exam", "date": datetime.now().isoformat(),
        "max_score": 20, "weight": 1, "class_id": class_id, "subject_id": subject_id, "term_id": term_id,
    }, headers=headers).json()["id"]
    return headers, class_id, term_id, subject_id, assessment_id


def test_assessments_are_isolated_by_school():
    a_headers, a_class, _a_term, _a_subject, a_assessment = _setup_school("grade_a")
    b_headers, b_class, b_term, b_subject, _b_assessment = _setup_school("grade_b")

    # Owner can read its own assessment.
    assert client.get(f"/grades/assessments/{a_assessment}", headers=a_headers).status_code == 200

    # School B cannot read, update, delete, or read grades of School A's assessment.
    assert client.get(f"/grades/assessments/{a_assessment}", headers=b_headers).status_code == 404
    assert client.get(f"/grades/assessments/{a_assessment}/grades", headers=b_headers).status_code == 404
    # Valid payload (B's own class/subject/term) so the 404 is tenant scoping, not validation.
    assert client.put(f"/grades/assessments/{a_assessment}", headers=b_headers, json={
        "title": "Hacked", "type": "exam", "date": datetime.now().isoformat(),
        "max_score": 20, "weight": 1, "class_id": b_class, "subject_id": b_subject, "term_id": b_term,
    }).status_code == 404
    assert client.delete(f"/grades/assessments/{a_assessment}", headers=b_headers).status_code == 404

    # School B cannot create an assessment against School A's class.
    assert client.post("/grades/assessments", headers=b_headers, json={
        "title": "X", "type": "exam", "date": datetime.now().isoformat(),
        "max_score": 20, "weight": 1, "class_id": a_class, "subject_id": b_subject, "term_id": b_term,
    }).status_code == 404

    # The assessment still exists for its owner after the rejected attacks.
    assert client.get(f"/grades/assessments/{a_assessment}", headers=a_headers).status_code == 200
