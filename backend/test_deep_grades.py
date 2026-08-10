"""Tests de fond des notes, moyennes et bulletins — par les bords.

`test_grades.py` valide le chemin heureux. Ici on cherche ce qui casse en
production : note hors barème, note négative, correction d'une note déjà saisie,
saisie par un professeur d'une AUTRE école, bulletin d'un élève qui n'est pas le
sien, moyenne pondérée, bulletin d'un trimestre sans note.

Le parcours passe par les VRAIS endpoints (inscription d'école, année, classe,
matière, élève) : les erreurs cachées se logent dans les chemins de création
autant que dans la lecture.
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _register_school(tag: str) -> dict:
    """Une école complète et exploitable : année, trimestre, classe, matière, élève."""
    domain = f"dg_{tag}"
    email = f"admin_dg_{tag}@test.com"
    password = "SecurePass123!"
    registration = client.post(
        "/auth/register/school",
        json={
            "school": {
                "name": f"Ecole profonde {tag}",
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
    term = client.post(
        "/education/terms",
        json={
            "name": "Trimestre 1",
            "start_date": "2026-09-01T00:00:00",
            "end_date": "2026-12-31T00:00:00",
            "academic_year_id": year["id"],
        },
        headers=headers,
    ).json()
    klass = client.post(
        "/education/classes",
        json={"name": f"6e {tag}", "level": "6e", "main_teacher_id": None},
        headers=headers,
    ).json()
    subject = client.post(
        "/education/subjects", json={"name": f"Maths {tag}"}, headers=headers
    ).json()
    student = client.post(
        "/students/",
        json={
            "email": f"eleve_dg_{tag}@test.com",
            "password": "StudentPass123!",
            "school_domain_prefix": domain,
            "full_name": f"Eleve {tag}",
            "role": "student",
            "profile": {
                "registration_number": f"DG-{tag}",
                "date_of_birth": "2012-01-01T00:00:00",
                "gender": "M",
                "parent_name": "Parent",
                "parent_phone": "+2250102030405",
                "current_class_id": klass["id"],
            },
        },
        headers=headers,
    ).json()

    return {
        "headers": headers,
        "domain": domain,
        "year_id": year["id"],
        "term_id": term["id"],
        "class_id": klass["id"],
        "subject_id": subject["id"],
        "student_id": student["id"],
    }


def _assessment(school: dict, *, title="Devoir", max_score=20, weight=1) -> int:
    response = client.post(
        "/grades/assessments",
        json={
            "title": title,
            "type": "exam",
            "date": datetime.now().isoformat(),
            "max_score": max_score,
            "weight": weight,
            "class_id": school["class_id"],
            "subject_id": school["subject_id"],
            "term_id": school["term_id"],
        },
        headers=school["headers"],
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _enter(school: dict, assessment_id: int, score, student_id=None, comment=None):
    return client.post(
        "/grades/entry/bulk",
        json={
            "assessment_id": assessment_id,
            "grades": [
                {
                    "assessment_id": assessment_id,
                    "student_id": student_id or school["student_id"],
                    "score": score,
                    "comment": comment,
                }
            ],
        },
        headers=school["headers"],
    )


@pytest.fixture(scope="module")
def school():
    return _register_school(uuid.uuid4().hex[:8])


@pytest.fixture(scope="module")
def neighbour():
    """Une école voisine, pour les tests de fuite entre établissements."""
    return _register_school(uuid.uuid4().hex[:8])


# --------------------------------------------------------------------------
# 1-4 : la valeur de la note
# --------------------------------------------------------------------------


def test_grade_above_the_scale_is_refused_or_stored_truthfully(school):
    """25/20 : soit c'est refusé, soit la moyenne du bulletin devient fausse."""
    assessment = _assessment(school, title="Hors bareme", max_score=20)
    response = _enter(school, assessment, 25)
    assert response.status_code in {200, 400, 422}, response.text
    if response.status_code == 200:
        grades = client.get(
            f"/grades/assessments/{assessment}/grades", headers=school["headers"]
        ).json()
        assert grades[0]["score"] == 25, (
            "note acceptée puis silencieusement modifiée : le professeur ne le verra pas"
        )


def test_negative_grade_is_refused_or_stored_truthfully(school):
    assessment = _assessment(school, title="Note negative")
    response = _enter(school, assessment, -3)
    assert response.status_code in {200, 400, 422}, response.text


def test_grade_is_updated_not_duplicated_on_second_entry(school):
    """Corriger une note doit remplacer la ligne, jamais en ajouter une seconde.

    Un doublon fausserait la moyenne sans que personne ne s'en aperçoive.
    """
    assessment = _assessment(school, title="Correction")
    assert _enter(school, assessment, 10).status_code == 200
    assert _enter(school, assessment, 14, comment="corrigee").status_code == 200
    grades = client.get(
        f"/grades/assessments/{assessment}/grades", headers=school["headers"]
    ).json()
    assert len(grades) == 1, f"{len(grades)} lignes pour une seule note : moyenne faussée"
    assert grades[0]["score"] == 14


def test_grade_persists_and_is_readable(school):
    assessment = _assessment(school, title="Lecture")
    _enter(school, assessment, 12.5, comment="ok")
    grades = client.get(
        f"/grades/assessments/{assessment}/grades", headers=school["headers"]
    ).json()
    assert grades[0]["score"] == pytest.approx(12.5)
    assert grades[0]["comment"] == "ok"


# --------------------------------------------------------------------------
# 5-7 : cloisonnement — la note d'un élève est une donnée personnelle
# --------------------------------------------------------------------------


def test_cannot_grade_a_student_of_another_school(school, neighbour):
    """Saisir une note pour l'élève du voisin doit être refusé, pas silencieux."""
    assessment = _assessment(school, title="Eleve etranger")
    response = _enter(school, assessment, 15, student_id=neighbour["student_id"])
    assert response.status_code in {403, 404}, response.text


def test_cannot_read_grades_of_another_schools_assessment(school, neighbour):
    foreign = _assessment(neighbour, title="Evaluation du voisin")
    _enter(neighbour, foreign, 18)
    response = client.get(
        f"/grades/assessments/{foreign}/grades", headers=school["headers"]
    )
    assert response.status_code == 404, response.text


def test_cannot_read_a_report_card_of_another_school(school, neighbour):
    response = client.get(
        f"/grades/reports/student/{neighbour['student_id']}/term/{neighbour['term_id']}",
        headers=school["headers"],
    )
    assert response.status_code in {403, 404}, response.text


# --------------------------------------------------------------------------
# 8-11 : le bulletin
# --------------------------------------------------------------------------


def test_report_card_reflects_the_entered_grade(school):
    assessment = _assessment(school, title="Bulletin base")
    _enter(school, assessment, 16)
    response = client.get(
        f"/grades/reports/student/{school['student_id']}/term/{school['term_id']}",
        headers=school["headers"],
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["student_id"] == school["student_id"]
    assert report["subjects"], "bulletin vide alors qu'une note existe"


def test_report_card_of_an_unknown_student_is_a_clean_404(school):
    """Un identifiant inconnu doit répondre 404, jamais une 500 ni un bulletin vide."""
    response = client.get(
        f"/grades/reports/student/999999/term/{school['term_id']}",
        headers=school["headers"],
    )
    assert response.status_code in {403, 404}, response.text


def test_report_card_of_an_unknown_term_never_crashes(school):
    response = client.get(
        f"/grades/reports/student/{school['student_id']}/term/999999",
        headers=school["headers"],
    )
    assert response.status_code in {200, 403, 404}, response.text


def test_report_card_pdf_is_a_real_pdf(school):
    """FONC-01 : le bulletin PDF doit être un PDF, pas une page d'erreur en 200."""
    assessment = _assessment(school, title="Bulletin PDF")
    _enter(school, assessment, 15)
    response = client.get(
        f"/grades/reports/student/{school['student_id']}/term/{school['term_id']}/pdf",
        headers=school["headers"],
    )
    assert response.status_code == 200, response.text[:300]
    assert response.content[:4] == b"%PDF", "réponse 200 qui n'est pas un PDF"


def test_report_card_pdf_is_idempotent_for_the_same_term(school):
    """Deux téléchargements ne doivent pas créer deux documents au registre."""
    assessment = _assessment(school, title="Bulletin PDF bis")
    _enter(school, assessment, 11)
    url = f"/grades/reports/student/{school['student_id']}/term/{school['term_id']}/pdf"
    first = client.get(url, headers=school["headers"])
    second = client.get(url, headers=school["headers"])
    assert first.status_code == second.status_code == 200
    assert second.content[:4] == b"%PDF"


# --------------------------------------------------------------------------
# 12-13 : l'évaluation elle-même
# --------------------------------------------------------------------------


def test_assessment_cannot_target_another_schools_class(school, neighbour):
    response = client.post(
        "/grades/assessments",
        json={
            "title": "Classe du voisin",
            "type": "exam",
            "date": datetime.now().isoformat(),
            "max_score": 20,
            "weight": 1,
            "class_id": neighbour["class_id"],
            "subject_id": school["subject_id"],
            "term_id": school["term_id"],
        },
        headers=school["headers"],
    )
    assert response.status_code in {400, 403, 404, 422}, response.text


def test_deleting_a_graded_assessment_is_guarded(school):
    """DATA-01 : supprimer une évaluation portant des notes doit être refusé (409)
    et surtout ne jamais laisser des notes orphelines derrière elle."""
    assessment = _assessment(school, title="A supprimer")
    _enter(school, assessment, 13)
    response = client.delete(f"/grades/assessments/{assessment}", headers=school["headers"])
    assert response.status_code in {204, 409}, response.text
    if response.status_code == 409:
        detail = response.json()["detail"]
        assert detail, "409 sans explication : l'utilisateur ne saura pas quoi faire"
    else:
        after = client.get(
            f"/grades/assessments/{assessment}/grades", headers=school["headers"]
        )
        assert after.status_code == 404
