import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _admin():
    unique_id = uuid.uuid4().hex[:8]
    email = f"admin_{unique_id}@test.com"
    password = "SecurePass123!"
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


def test_school_localization_settings_use_country_defaults():
    headers, _unique_id = _admin()

    countries = client.get("/system/localization/countries", headers=headers)
    assert countries.status_code == 200
    assert countries.json()["countries"]["CI"]["currency"] == "FCFA"
    assert countries.json()["countries"]["GB"]["currency"] == "GBP"

    updated = client.put("/system/school-settings", headers=headers, json={
        "country_code": "GB",
        "phone": "07700900123",
        "address_structured": {
            "street": "10 Downing Street",
            "city": "London",
            "region": "England",
            "postal_code": "SW1A 2AA",
        },
    })
    assert updated.status_code == 200
    data = updated.json()
    assert data["default_currency"] == "GBP"
    assert data["currency_code"] == "GBP"
    assert data["primary_language"] == "en"
    assert data["phone_e164"] == "+447700900123"
    assert "London" in data["formatted_address"]


def test_settings_user_management_subscription_and_role_deduplication():
    headers, unique_id = _admin()

    settings = client.put("/system/school-settings", headers=headers, json={
        "name": f"Persistent School {unique_id}",
        "phone": "+2250700000000",
        "email": f"school-{unique_id}@example.com",
        "website": "https://example.com",
        "address_structured": {
            "street": "1 Rue de la Paix",
            "district": "Plateau",
            "city": "Abidjan",
            "region": "Abidjan",
            "country": "Côte d'Ivoire",
            "latitude": 5.36,
            "longitude": -4.0083,
        },
    })
    assert settings.status_code == 200, settings.text
    persisted = client.get("/system/school-settings", headers=headers)
    assert persisted.status_code == 200
    assert persisted.json()["name"] == f"Persistent School {unique_id}"
    assert persisted.json()["address_structured"]["district"] == "Plateau"
    logo = client.post(
        "/system/school-settings/logo",
        headers=headers,
        files={"logo": ("logo.png", b"\x89PNG\r\n\x1a\nTeducAI", "image/png")},
    )
    assert logo.status_code == 200, logo.text
    assert logo.json()["logo_url"].endswith("/logo")
    public_logo = client.get(logo.json()["logo_url"])
    assert public_logo.status_code == 200

    free_plan = client.post("/system/subscription/change", headers=headers, json={
        "plan": "free",
        "billing_cycle": "monthly",
        "payment_provider": "manual",
    })
    assert free_plan.status_code == 200, free_plan.text
    assert free_plan.json()["subscription"]["status"] == "active"

    paid_plan = client.post("/system/subscription/change", headers=headers, json={
        "plan": "pro",
        "billing_cycle": "yearly",
        "payment_provider": "manual",
    })
    assert paid_plan.status_code == 200, paid_plan.text
    assert paid_plan.json()["subscription"]["status"] == "pending_payment"
    current_plan = client.get("/system/subscription", headers=headers)
    assert current_plan.status_code == 200
    assert current_plan.json()["plan"] == "pro"

    created = client.post("/system/users", headers=headers, json={
        "email": f"managed-{unique_id}@example.com",
        "full_name": "Managed User",
        "password": "SecurePass123!",
        "role": "teacher",
        "role_keys": ["teacher"],
    })
    assert created.status_code == 200, created.text
    user_id = created.json()["id"]

    updated = client.put(f"/system/users/{user_id}", headers=headers, json={
        "full_name": "Managed User Updated",
        "phone_number": "+2250102030405",
        "role": "teacher",
        "role_keys": ["teacher", "educator"],
    })
    assert updated.status_code == 200, updated.text
    details = client.get(f"/system/users/{user_id}", headers=headers)
    assert details.status_code == 200
    assert details.json()["full_name"] == "Managed User Updated"
    assert set(details.json()["role_keys"]) == {"teacher", "educator"}

    photo = client.post(
        f"/system/users/{user_id}/profile-photo",
        headers=headers,
        files={"photo": ("profile.png", b"\x89PNG\r\n\x1a\nTeducAI profile", "image/png")},
    )
    assert photo.status_code == 200, photo.text
    assert photo.json()["profile_photo_url"].endswith("/profile-photo")
    protected_photo = client.get(photo.json()["profile_photo_url"], headers=headers)
    assert protected_photo.status_code == 200
    assert protected_photo.headers["content-type"].startswith("image/png")
    anonymous_photo = client.get(photo.json()["profile_photo_url"])
    assert anonymous_photo.status_code == 401

    deleted = client.delete(f"/system/users/{user_id}", headers=headers)
    assert deleted.status_code == 204, deleted.text
    users = client.get("/system/users", headers=headers)
    assert users.status_code == 200
    assert user_id not in {row["id"] for row in users.json()}

    catalog = client.get("/system/permissions/catalog", headers=headers)
    assert catalog.status_code == 200
    role_keys = catalog.json()["roles"]
    assert len(role_keys) == len(set(role_keys))
