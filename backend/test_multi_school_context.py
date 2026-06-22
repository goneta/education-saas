import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _admin(prefix: str):
    password = "SecurePass123!"
    unique = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique}@test.com"
    response = client.post("/auth/register/school", json={
        "school": {
            "name": f"Groupe {prefix} {unique}",
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
    assert response.status_code == 200
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return response.json(), {"Authorization": f"Bearer {token}"}


def test_multi_model_context_is_seeded_scoped_and_not_forgeable():
    school_a, headers_a = _admin("context_a")
    school_b, headers_b = _admin("context_b")

    primary = client.post(
        f"/system/schools/{school_a['id']}/apply-template",
        headers=headers_a,
        json={"template": "primary"},
    )
    assert primary.status_code == 200
    primary_assignment_id = primary.json()["school_model_assignment_id"]

    technical = client.post("/context/assignments", headers=headers_a, json={
        "school_id": school_a["id"],
        "model_codes": ["TECHNICAL"],
        "seed_defaults": True,
    })
    assert technical.status_code == 200
    technical_assignment_id = technical.json()["assignments"][0]["id"]

    duplicate_seed = client.post("/context/assignments", headers=headers_a, json={
        "school_id": school_a["id"],
        "model_codes": ["TECHNICAL"],
        "seed_defaults": True,
    })
    assert duplicate_seed.status_code == 200
    assert sum(duplicate_seed.json()["seeded"]["TECHNICAL"].values()) == 0

    switched = client.put("/context/active", headers=headers_a, json={
        "school_model_assignment_id": technical_assignment_id,
    })
    assert switched.status_code == 200
    assert switched.json()["model_code"] == "TECHNICAL"

    technical_headers = {**headers_a, "X-School-Model-Assignment-ID": str(technical_assignment_id)}
    technical_classes = client.get("/education/classes", headers=technical_headers)
    assert technical_classes.status_code == 200
    assert {row["name"] for row in technical_classes.json()} >= {"BTS 1", "BTS 2"}

    primary_headers = {**headers_a, "X-School-Model-Assignment-ID": str(primary_assignment_id)}
    primary_classes = client.get("/education/classes", headers=primary_headers)
    assert primary_classes.status_code == 200
    assert {row["name"] for row in primary_classes.json()} >= {"CP1", "CM2"}
    assert "BTS 1" not in {row["name"] for row in primary_classes.json()}

    school_b_options = client.get("/context/options", headers=headers_b).json()
    foreign_assignment_id = school_b_options["assignments"][0]["id"]
    forbidden = client.put("/context/active", headers=headers_a, json={
        "school_model_assignment_id": foreign_assignment_id,
    })
    assert forbidden.status_code == 403

    options_a = client.get("/context/options", headers=headers_a).json()
    organization_id = options_a["schools"][0]["organization_id"]
    second_school = client.post("/context/schools", headers=headers_a, json={
        "organization_id": organization_id,
        "school": {
            "name": "Campus professionnel",
            "domain_prefix": f"campus_{uuid.uuid4().hex[:8]}",
            "school_type": "professional",
            "address": "Bouake",
        },
        "model_codes": ["PROFESSIONAL", "VOCATIONAL"],
        "seed_defaults": True,
    })
    assert second_school.status_code == 200
    assert {row["model_code"] for row in second_school.json()["assignments"]} == {"PROFESSIONAL", "VOCATIONAL"}
    refreshed_options = client.get("/context/options", headers=headers_a).json()
    visible_school_ids = {row["id"] for row in refreshed_options["schools"]}
    assert school_a["id"] in visible_school_ids
    assert second_school.json()["id"] in visible_school_ids
    assert school_b["id"] not in visible_school_ids
