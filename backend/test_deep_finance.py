"""Tests de fond du cycle de vie Finance — frais, encaissements, journal de caisse.

Campagne « erreurs avalées en silence » : la suite existante couvrait surtout le
chemin heureux. Ici on attaque les **bords** — c'est là que se cachent les
pannes que l'utilisateur découvre en production : montant négatif, sur-paiement,
résidu flottant qui bloque un certificat, encaissement contre le frais d'une
AUTRE école, journal de caisse, filtres de date, plafond de pagination.

Chaque test nomme le risque métier qu'il verrouille.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, security
from backend.main import app


def _school(db, tag: str):
    org = models.Organization(name=f"Org {tag}")
    db.add(org)
    db.flush()
    school = models.School(
        name=f"Ecole {tag}",
        domain_prefix=f"s{tag}",
        school_type=models.SchoolType.GENERAL,
        organization_id=org.id,
    )
    db.add(school)
    db.flush()
    # Une ecole reelle a TOUJOURS un modele actif : /finance/fees filtre dessus
    # (400 explicite sinon). Une fixture sans modele testerait une ecole qui
    # n'existe pas en production.
    model = models.SchoolModel(code=f"MOD{tag}", name=f"Modele {tag}")
    db.add(model)
    db.flush()
    sma = models.SchoolModelAssignment(
        school_id=school.id, school_model_id=model.id, is_active=True
    )
    db.add(sma)
    db.flush()
    school._sma_id = sma.id
    return school


def _admin(db, school, tag: str):
    user = models.User(
        email=f"admin{tag}@x.com",
        hashed_password="x",
        full_name=f"Admin {tag}",
        role=models.UserRole.SCHOOL_ADMIN,
        school_id=school.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _student(db, school, tag: str):
    user = models.User(
        email=f"eleve{tag}@x.com",
        hashed_password="x",
        full_name=f"Eleve {tag}",
        role=models.UserRole.STUDENT,
        school_id=school.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    profile = models.StudentProfile(user_id=user.id, status=models.StudentStatus.ASSIGNED)
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture
def ctx():
    """Deux écoles complètes : celle de l'appelant, et une voisine (fuite de données)."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    database.Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()

    mine = _school(db, "A")
    other = _school(db, "B")
    admin = _admin(db, mine, "A")
    other_admin = _admin(db, other, "B")
    student = _student(db, mine, "A")
    other_student = _student(db, other, "B")
    db.commit()

    app.dependency_overrides[database.get_db] = lambda: db
    app.dependency_overrides[security.get_current_user] = lambda: admin
    client = TestClient(app, raise_server_exceptions=False)

    state = {
        "client": client,
        "db": db,
        "school": mine,
        "other_school": other,
        "admin": admin,
        "other_admin": other_admin,
        "student": student,
        "other_student": other_student,
    }
    yield state
    app.dependency_overrides.clear()
    db.close()


def _make_fee(db, school, student, *, amount=100_000.0, title="Scolarite T1", category="tuition"):
    fee = models.Fee(
        title=title,
        amount=amount,
        status=models.FeeStatus.PENDING,
        category=category,
        student_id=student.id if student else None,
        school_id=school.id,
        school_model_assignment_id=school._sma_id,
        due_date=datetime.utcnow() + timedelta(days=30),
    )
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee


def _pay(client, fee_id, amount, **extra):
    body = {"amount": amount, "payment_method": "cash"}
    body.update(extra)
    return client.post(f"/finance/fees/{fee_id}/payments", json=body)


# --------------------------------------------------------------------------
# 1-4 : le montant encaissé
# --------------------------------------------------------------------------


def test_negative_payment_is_refused(ctx):
    """Un encaissement négatif serait un remboursement déguisé, hors piste d'audit."""
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"])
    assert _pay(ctx["client"], fee.id, -5000).status_code == 400


def test_zero_payment_is_refused(ctx):
    """Zéro FCFA fabriquerait un reçu pour un encaissement inexistant."""
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"])
    assert _pay(ctx["client"], fee.id, 0).status_code == 400


def test_overpayment_is_refused(ctx):
    """Encaisser plus que le solde crée un avoir invisible dans les comptes."""
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=50_000)
    assert _pay(ctx["client"], fee.id, 50_001).status_code == 400


def test_second_payment_cannot_exceed_the_remaining_balance(ctx):
    """Le solde restant doit tenir compte des encaissements DÉJÀ passés."""
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=50_000)
    assert _pay(ctx["client"], fee.id, 30_000).status_code == 200
    assert _pay(ctx["client"], fee.id, 25_000).status_code == 400
    assert _pay(ctx["client"], fee.id, 20_000).status_code == 200


# --------------------------------------------------------------------------
# 5-7 : le statut du frais — ce qui débloque le certificat de l'élève
# --------------------------------------------------------------------------


def test_partial_payment_leaves_the_fee_partial(ctx):
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=100_000)
    body = _pay(ctx["client"], fee.id, 40_000).json()
    assert body["status"] == models.FeeStatus.PARTIAL.value
    assert body["total_paid"] == pytest.approx(40_000)


def test_full_payment_settles_the_fee(ctx):
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=100_000)
    body = _pay(ctx["client"], fee.id, 100_000).json()
    assert body["status"] == models.FeeStatus.PAID.value


def test_float_residue_still_settles_the_fee(ctx):
    """MONEY-02 : trois tiers de 100 000 laissent un résidu binaire.

    Sans la tolérance de `services/money.py`, le frais restait PARTIAL pour
    ~1e-11 FCFA — et l'élève se voyait refuser son certificat de scolarité.
    """
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=100_000)
    third = 100_000 / 3
    _pay(ctx["client"], fee.id, third)
    _pay(ctx["client"], fee.id, third)
    body = _pay(ctx["client"], fee.id, 100_000 - 2 * third).json()
    assert body["status"] == models.FeeStatus.PAID.value, body


# --------------------------------------------------------------------------
# 8-9 : cloisonnement entre établissements
# --------------------------------------------------------------------------


def test_cannot_pay_a_fee_of_another_school(ctx):
    """Un caissier ne doit même pas pouvoir DÉSIGNER le frais d'une autre école."""
    foreign = _make_fee(ctx["db"], ctx["other_school"], ctx["other_student"])
    assert _pay(ctx["client"], foreign.id, 1_000).status_code == 404


def test_fee_list_never_leaks_another_school(ctx):
    _make_fee(ctx["db"], ctx["school"], ctx["student"], title="Chez moi")
    _make_fee(ctx["db"], ctx["other_school"], ctx["other_student"], title="Chez le voisin")
    response = ctx["client"].get("/finance/fees")
    assert response.status_code == 200, response.text
    titles = [f["title"] for f in response.json()]
    assert "Chez moi" in titles
    assert "Chez le voisin" not in titles


# --------------------------------------------------------------------------
# 10-12 : journal de caisse et liste des paiements (l'écran cassé du Lot 6)
# --------------------------------------------------------------------------


def test_cash_journal_answers_and_totals_the_day(ctx):
    """`GET /finance/cash-journal` renvoyait 500 — l'écran de clôture quotidien."""
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=80_000)
    _pay(ctx["client"], fee.id, 30_000)
    response = ctx["client"].get("/finance/cash-journal")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == pytest.approx(30_000)
    assert len(payload["payments"]) == 1


def test_cash_journal_ignores_payments_outside_the_window(ctx):
    """Une clôture qui compte la veille fausse le fond de caisse remis."""
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=80_000)
    _pay(ctx["client"], fee.id, 30_000)
    yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
    payload = ctx["client"].get(
        f"/finance/cash-journal?start_date={yesterday}&end_date={yesterday}"
    ).json()
    assert payload["total"] == pytest.approx(0)
    assert payload["payments"] == []


def test_payment_list_publishes_the_total_and_paginates(ctx):
    """PERF-07 : le total exact vit dans `X-Total-Count`, pas dans la page."""
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=100_000)
    for _ in range(5):
        _pay(ctx["client"], fee.id, 10_000)
    response = ctx["client"].get("/finance/payments?limit=2")
    assert response.status_code == 200, response.text
    assert response.headers["X-Total-Count"] == "5"
    assert len(response.json()) == 2
    # Sans limite, le comportement historique est inchangé : tout est renvoyé.
    assert len(ctx["client"].get("/finance/payments").json()) == 5


def test_payment_list_is_school_scoped(ctx):
    """La liste alimente la comptabilité : une ligne étrangère fausserait les comptes."""
    mine = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=10_000)
    foreign = _make_fee(ctx["db"], ctx["other_school"], ctx["other_student"], amount=10_000)
    _pay(ctx["client"], mine.id, 5_000)
    app.dependency_overrides[security.get_current_user] = lambda: ctx["other_admin"]
    _pay(ctx["client"], foreign.id, 7_000)
    app.dependency_overrides[security.get_current_user] = lambda: ctx["admin"]

    payments = ctx["client"].get("/finance/payments").json()
    assert [p["amount"] for p in payments] == [pytest.approx(5_000)]


def test_deleting_a_fee_with_payments_does_not_silently_lose_the_money(ctx):
    """Supprimer un frais encaissé ne doit jamais laisser un paiement orphelin.

    Soit c'est refusé, soit les paiements partent avec — mais JAMAIS une ligne
    de paiement qui pointe vers un frais disparu (elle casserait le journal,
    qui joint Payment→Fee).
    """
    fee = _make_fee(ctx["db"], ctx["school"], ctx["student"], amount=20_000)
    _pay(ctx["client"], fee.id, 20_000)
    response = ctx["client"].delete(f"/finance/fees/{fee.id}")
    assert response.status_code in {200, 409}
    if response.status_code == 200:
        orphans = (
            ctx["db"].query(models.Payment)
            .outerjoin(models.Fee, models.Payment.fee_id == models.Fee.id)
            .filter(models.Fee.id.is_(None))
            .count()
        )
        assert orphans == 0, "paiement orphelin : le journal de caisse plantera"
    assert ctx["client"].get("/finance/cash-journal").status_code == 200
