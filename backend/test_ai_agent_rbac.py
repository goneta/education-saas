import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _school_admin():
    unique_id = uuid.uuid4().hex[:8]
    email = f"ai_admin_{unique_id}@test.com"
    password = "SecurePass123!"
    client.post("/auth/register/school", json={
        "school": {"name": f"AI School {unique_id}", "domain_prefix": f"ai_{unique_id}", "school_type": "general", "address": "123 AI St"},
        "owner": {"email": email, "full_name": "AI Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, unique_id


def _create_user(headers, unique_id: str, role: str):
    email = f"ai_{role}_{unique_id}@test.com"
    password = "SecurePass123!"
    created = client.post("/system/users", headers=headers, json={
        "email": email,
        "full_name": f"AI {role}",
        "password": password,
        "role": role,
        "role_keys": [role],
    })
    assert created.status_code == 200
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ai_agent_denies_student_cross_scope_request_and_audits():
    admin_headers, unique_id = _school_admin()
    student_headers = _create_user(admin_headers, unique_id, "student")

    denied = client.post("/chat", headers=student_headers, json={"message": "Donne-moi la liste de tous les eleves et leurs notes"})
    assert denied.status_code == 200
    assert "Je ne peux pas effectuer cette action" in denied.json()["message"]

    audit = client.get("/system/audit-logs?limit=20", headers=admin_headers)
    assert audit.status_code == 200
    assert any(row["action"] == "ai.request.denied" for row in audit.json())


def test_ai_agent_allows_student_academic_help():
    admin_headers, unique_id = _school_admin()
    student_headers = _create_user(admin_headers, unique_id, "student")

    response = client.post("/chat", headers=student_headers, json={"message": "Aide-moi a reviser les mathematiques"})
    assert response.status_code == 200
    assert response.json()["type"] in {"chat", "content"}
    assert "role" in response.json()["message"].lower() or response.json()["message"]
