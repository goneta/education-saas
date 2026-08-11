"""Tests de fond des présences — la table la plus volumineuse et la plus sensible.

Volumétrie : une école de 800 élèves produit ~700 000 lignes par année scolaire.
Vie privée : savoir qui était absent quel jour est une donnée personnelle d'enfant.
Les deux se sont déjà mal passées (BUG-D : liste sans limite NI portée).

On attaque : l'appel deux fois de suite (doublon = absence comptée double),
l'élève d'une autre école, le créneau d'une autre école, la pagination, le
plafond, les statistiques, et la lecture par un élève / un parent.
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _school(tag: str) -> dict:
    domain = f"da_{tag}"
    email = f"admin_da_{tag}@test.com"
    password = "SecurePass123!"
    registration = client.post(
        "/auth/register/school",
        json={
            "school": {
                "name": f"Ecole presences {tag}",
                "domain_prefix": domain,
                "school_type": "general",
                "address": "1 rue des tests",
            },
            "owner": {
                "email": email,
                "full_name": "Admin",
                "role": "school_admin",
                "password": password,
            },
        },
    )
    assert registration.status_code == 200, registration.text
    token = client.post(
        "/auth/token", data={"username": email, "password": password}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    year = client.post(
        "/education/academic-years",
        json={
            "name": f"2026-2027 {tag}",
            "start_date": "2026-09-01T00:00:00",
            "end_date": "2027-06-30T00:00:00",
            "is_current": True,
        },
        headers=headers,
    ).json()
    klass = client.post(
        "/education/classes",
        json={"name": f"5e {tag}", "level": "5e", "main_teacher_id": None},
        headers=headers,
    ).json()
    subject = client.post(
        "/education/subjects", json={"name": f"Histoire {tag}"}, headers=headers
    ).json()
    slot = client.post(
        "/education/timetables",
        json={
            "day_of_week": "monday",
            "start_time": "08:00:00",
            "end_time": "09:00:00",
            "room": "A1",
            "class_id": klass["id"],
            "subject_id": subject["id"],
            "teacher_id": None,
        },
        headers=headers,
    )
    assert slot.status_code in {200, 201}, slot.text
    student = client.post(
        "/students/",
        json={
            "email": f"eleve_da_{tag}@test.com",
            "password": "StudentPass123!",
            "school_domain_prefix": domain,
            "full_name": f"Eleve {tag}",
            "role": "student",
            "profile": {
                "registration_number": f"DA-{tag}",
                "date_of_birth": "2012-01-01T00:00:00",
                "gender": "F",
                "parent_name": "Parent",
                "parent_phone": "+2250102030405",
                "current_class_id": klass["id"],
            },
        },
        headers=headers,
    ).json()

    profile = (student.get("student_profile") or {})
    return {
        "headers": headers,
        "class_id": klass["id"],
        # `/students/` renvoie le COMPTE (User) ; les presences referencent le
        # PROFIL eleve. Confondre les deux fabrique de faux positifs.
        "profile_id": profile.get("id"),
        "timetable_id": slot.json()["id"],
        "student_id": student["id"],
        "student_email": f"eleve_da_{tag}@test.com",
        "year_id": year["id"],
    }


def _mark(school, status, *, student_id=None, timetable_id=None, date=None, remarks=None):
    return client.post(
        "/attendance/batch",
        json={
            "timetable_id": timetable_id or school["timetable_id"],
            "date": date or datetime(2026, 9, 7).isoformat(),
            "students": [
                {
                    # profil eleve, pas l'id de compte : les deux ne coincident
                    # que tant que les sequences d'id se suivent par hasard.
                    "student_id": student_id or school["profile_id"],
                    "status": status,
                    "remarks": remarks,
                }
            ],
        },
        headers=school["headers"],
    )


@pytest.fixture(scope="module")
def school():
    return _school(uuid.uuid4().hex[:8])


@pytest.fixture(scope="module")
def neighbour():
    return _school(uuid.uuid4().hex[:8])


# --------------------------------------------------------------------------
# 1-4 : l'appel lui-même
# --------------------------------------------------------------------------


def test_marking_a_student_present_works(school):
    response = _mark(school, "present")
    assert response.status_code == 200, response.text
    assert response.json()[0]["status"] == "present"


def test_calling_twice_updates_instead_of_duplicating(school):
    """Refaire l'appel ne doit pas créer une seconde ligne.

    Un doublon compterait l'absence deux fois : relance aux parents et
    statistiques faussées, sans aucun message d'erreur.
    """
    date = datetime(2026, 9, 8).isoformat()
    _mark(school, "present", date=date)
    _mark(school, "absent", date=date)
    records = client.get(
        f"/attendance/?timetable_id={school['timetable_id']}", headers=school["headers"]
    ).json()
    same_day = [r for r in records if r["date"].startswith("2026-09-08")]
    assert len(same_day) == 1, f"{len(same_day)} lignes pour un seul appel"
    assert same_day[0]["status"] == "absent"


def test_an_invalid_status_is_refused(school):
    """Un statut inconnu doit être refusé par la validation, pas stocké tel quel."""
    response = _mark(school, "peut-etre")
    assert response.status_code in {400, 422}, response.text


def test_remarks_are_persisted(school):
    """La remarque justifie l'absence auprès des parents — elle ne doit pas se perdre."""
    date = datetime(2026, 9, 9).isoformat()
    _mark(school, "excused", date=date, remarks="Certificat medical")
    records = client.get(
        f"/attendance/?timetable_id={school['timetable_id']}", headers=school["headers"]
    ).json()
    day = [r for r in records if r["date"].startswith("2026-09-09")]
    assert day and day[0]["remarks"] == "Certificat medical"


# --------------------------------------------------------------------------
# 5-7 : cloisonnement
# --------------------------------------------------------------------------


def test_cannot_mark_a_student_of_another_school(school, neighbour):
    response = _mark(school, "absent", student_id=neighbour["student_id"])
    assert response.status_code in {403, 404}, response.text


def test_cannot_use_a_timetable_slot_of_another_school(school, neighbour):
    response = _mark(school, "absent", timetable_id=neighbour["timetable_id"])
    assert response.status_code == 404, response.text


def test_attendance_list_never_leaks_another_school(school, neighbour):
    _mark(neighbour, "absent", date=datetime(2026, 9, 10).isoformat())
    mine = client.get("/attendance/", headers=school["headers"]).json()
    foreign_ids = {
        r["id"]
        for r in client.get("/attendance/", headers=neighbour["headers"]).json()
    }
    assert not ({r["id"] for r in mine} & foreign_ids), "fuite de présences entre écoles"


# --------------------------------------------------------------------------
# 8-10 : volumétrie (BUG-D) et filtres
# --------------------------------------------------------------------------


def test_list_is_paginated_and_capped(school):
    """La liste renvoyait `query.all()` — ~700 000 lignes en une réponse."""
    response = client.get("/attendance/?limit=1", headers=school["headers"])
    assert response.status_code == 200
    assert len(response.json()) <= 1
    # Un plafond demandé au-delà de la limite dure ne doit pas la faire sauter.
    huge = client.get("/attendance/?limit=100000", headers=school["headers"])
    assert huge.status_code == 200
    assert len(huge.json()) <= 500, "le plafond de sécurité a sauté"


def test_pagination_does_not_repeat_a_row(school):
    """Sans tri déterministe, page 1 et page 2 peuvent renvoyer la même ligne."""
    for day in range(11, 16):
        _mark(school, "present", date=datetime(2026, 9, day).isoformat())
    first = client.get("/attendance/?limit=2&skip=0", headers=school["headers"]).json()
    second = client.get("/attendance/?limit=2&skip=2", headers=school["headers"]).json()
    assert not ({r["id"] for r in first} & {r["id"] for r in second}), (
        "chevauchement entre deux pages : tri non déterministe"
    )


def test_class_filter_is_honoured(school):
    # Ce test lisait une ligne créée par un test précédent : il échouait donc
    # seul, ou dès que l'ordre changeait. Un test qui dépend d'un autre ne peut
    # pas servir de barrière CI — il crée lui-même la donnée qu'il vérifie.
    seeded = _mark(school, "present", date=datetime(2026, 9, 21).isoformat())
    assert seeded.status_code == 200, seeded.text
    response = client.get(
        f"/attendance/?class_id={school['class_id']}", headers=school["headers"]
    )
    assert response.status_code == 200, response.text
    assert response.json(), "filtre par classe : aucune ligne alors qu'il en existe"


def test_unknown_class_filter_returns_empty_not_error(school):
    """Un filtre sans résultat est une liste vide, pas une 500."""
    response = client.get("/attendance/?class_id=999999", headers=school["headers"])
    assert response.status_code == 200, response.text
    assert response.json() == []


# --------------------------------------------------------------------------
# 11-12 : statistiques et vie privée
# --------------------------------------------------------------------------


def test_stats_require_a_class_and_then_answer(school):
    """`class_id` est obligatoire : sans lui, 422 explicite (jamais une 500)."""
    assert client.get("/attendance/stats", headers=school["headers"]).status_code == 422
    response = client.get(
        f"/attendance/stats?class_id={school['class_id']}", headers=school["headers"]
    )
    assert response.status_code == 200, response.text


def test_stats_of_another_schools_class_leak_nothing(school, neighbour):
    response = client.get(
        f"/attendance/stats?class_id={neighbour['class_id']}", headers=school["headers"]
    )
    assert response.status_code in {200, 403, 404}, response.text
    if response.status_code == 200:
        payload = response.json()
        assert all(
            not value for key, value in payload.items() if isinstance(value, (int, float))
        ), f"statistiques d'une classe étrangère renvoyées : {payload}"


def test_a_pupil_only_sees_their_own_attendance(school):
    """PRIV-01 : un élève connecté ne doit pas lire les absences de ses camarades."""
    token = client.post(
        "/auth/token",
        data={"username": school["student_email"], "password": "StudentPass123!"},
    )
    if token.status_code != 200:
        pytest.skip("compte élève non activable dans cet environnement")
    pupil_headers = {"Authorization": f"Bearer {token.json()['access_token']}"}
    response = client.get("/attendance/", headers=pupil_headers)
    assert response.status_code in {200, 403}, response.text
    if response.status_code == 200:
        others = [
            r for r in response.json() if r["student_id"] != school["profile_id"]
        ]
        assert not others, "un élève lit les présences des autres"
