import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _admin():
    unique_id = uuid.uuid4().hex[:8]
    email = f"admin_{unique_id}@test.com"
    password = "securepassword123"
    client.post("/auth/register/school", json={
        "school": {"name": f"Config School {unique_id}", "domain_prefix": f"config_{unique_id}", "school_type": "general", "address": "123 Config St"},
        "owner": {"email": email, "full_name": "Config Admin", "role": "school_admin", "password": password},
    })
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, unique_id


def test_system_config():
    headers, unique_id = _admin()

    levels = client.get("/system/reference-data/EDUCATION_LEVEL", headers=headers)
    assert levels.status_code == 200

    custom_payload = {
        "category": "EDUCATION_LEVEL",
        "key": f"CUSTOM_{unique_id}",
        "value": {"fr": "Classe Speciale", "en": "Special Class", "es": "Clase especial"},
        "order": 999,
    }
    created = client.post("/system/reference-data", json=custom_payload, headers=headers)
    assert created.status_code == 200
    assert created.json()["value"]["fr"] == "Classe Speciale"

    catalog = client.get("/system/permissions/catalog", headers=headers)
    assert catalog.status_code == 200
    assert "finance:read" in catalog.json()["permissions"]
