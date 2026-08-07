"""Filet anti-500 sur TOUTE la surface d'API — chasse aux erreurs cachées.

Pourquoi ce test existe : `GET /finance/cash-journal` renvoyait **HTTP 500** en
production (7 arguments positionnels passés à une signature de 11). Personne ne
l'a vu parce qu'aucun test ne l'appelait et parce que le frontend avalait
l'erreur en silence. Ce fichier rend ce type de panne impossible à cacher : il
énumère **toutes** les routes GET enregistrées dans l'application et vérifie
qu'aucune ne répond 500.

Ce qui est toléré (et pourquoi) :
- **422** : paramètre requis absent — c'est la validation qui fait son travail ;
- **404** : ressource inexistante dans une base vide — normal ;
- **400/403** : contexte ou droits manquants — décision métier explicite ;
- **503** : dépendance externe non configurée (SMTP, IA, passerelle) — refus
  honnête, jamais un faux succès.
Seul **500** (et toute exception non gérée) fait échouer le test : c'est la
signature d'un bug, pas d'une règle métier.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, security
from backend.main import app


ACCEPTABLE = {200, 201, 204, 302, 400, 401, 403, 404, 409, 422, 423, 429, 503}

# Routes exclues du balayage, avec la raison — jamais d'exclusion silencieuse.
SKIP_EXACT = {
    "/",                      # page d'accueil de l'API
    "/openapi.json",
    "/docs", "/redoc", "/docs/oauth2-redirect",
}
SKIP_PREFIXES = (
    "/files/download",        # renvoie un flux binaire depuis le stockage réel
    "/api/v1",                # API partenaire : authentifiée par clé, pas par JWT
)


_STATE = {}


@pytest.fixture(scope="module")
def db_session(api):
    """La session utilisée par l'application de test (pour la remettre à zéro)."""
    return _STATE["db"]


@pytest.fixture(scope="module")
def api():
    """Application réelle, base en mémoire, un Super Admin authentifié."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()

    tag = uuid.uuid4().hex[:6]
    org = models.Organization(name=f"Org {tag}")
    db.add(org); db.flush()
    school = models.School(name=f"Ecole {tag}", domain_prefix=f"s_{tag}",
                           school_type=models.SchoolType.GENERAL, organization_id=org.id)
    db.add(school); db.flush()
    model = models.SchoolModel(code=f"MOD-{tag}", name="Modèle")
    db.add(model); db.flush()
    db.add(models.SchoolModelAssignment(school_id=school.id, school_model_id=model.id, is_active=True))
    admin = models.User(email=f"admin_{tag}@x.com", hashed_password="x", full_name="Admin",
                        role=models.UserRole.SUPER_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()

    _STATE["db"] = db
    app.dependency_overrides[database.get_db] = lambda: db
    app.dependency_overrides[security.get_current_user] = lambda: admin
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()
    db.close()


def _get_routes() -> list[str]:
    """Toutes les routes GET sans paramètre de chemin (appelables telles quelles)."""
    paths = []
    for route in app.routes:
        methods = getattr(route, "methods", set()) or set()
        path = getattr(route, "path", "")
        if "GET" not in methods or "{" in path:
            continue
        if path in SKIP_EXACT or path.startswith(SKIP_PREFIXES):
            continue
        paths.append(path)
    return sorted(set(paths))


def test_the_scan_actually_covers_the_api():
    """Garde-fou du garde-fou : si l'énumération casse, le test doit crier."""
    routes = _get_routes()
    assert len(routes) > 80, f"seulement {len(routes)} routes GET balayées — énumération suspecte"
    # La route qui a motivé ce fichier doit être dans le lot.
    assert "/finance/cash-journal" in routes


@pytest.mark.parametrize("path", _get_routes())
def test_get_endpoint_never_returns_500(api, db_session, path):
    """Aucune route GET ne doit planter sur une base vide mais cohérente.

    La session est remise à zéro après chaque appel : une transaction laissée
    en échec par UN endpoint fautif empoisonnait sinon tous les suivants — la
    première exécution a produit 135 échecs pour **un seul** vrai bug."""
    try:
        response = api.get(path)
        assert response.status_code in ACCEPTABLE, (
            f"GET {path} -> HTTP {response.status_code}\n"
            f"Corps : {response.text[:400]}"
        )
    finally:
        db_session.rollback()


def test_cash_journal_regression_is_locked(api):
    """La panne d'origine, verrouillée nommément."""
    response = api.get("/finance/cash-journal")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert set(payload) >= {"payments", "total", "by_category", "by_operator"}


def test_health_and_readiness_answer(api):
    for path in ("/health", "/ready"):
        response = api.get(path)
        assert response.status_code in {200, 503}, f"{path} -> {response.status_code}"
