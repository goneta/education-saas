from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import ai_billing
from backend.services import ai_credits, payment_gateway


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _fixtures(db):
    school = models.School(name="Ecole Credits", domain_prefix="credits-test", school_type=models.SchoolType.GENERAL)
    super_admin = models.User(
        email="super-credit@test.local",
        hashed_password="test",
        full_name="Super Credit",
        role=models.UserRole.SUPER_ADMIN,
        is_active=True,
    )
    school_admin = models.User(
        email="admin-credit@test.local",
        hashed_password="test",
        full_name="Admin Credit",
        role=models.UserRole.SCHOOL_ADMIN,
        school=school,
        is_active=True,
    )
    teacher = models.User(
        email="teacher-credit@test.local",
        hashed_password="test",
        full_name="Teacher Credit",
        role=models.UserRole.TEACHER,
        school=school,
        is_active=True,
    )
    db.add_all([school, super_admin, school_admin, teacher])
    db.commit()
    return school, super_admin, school_admin, teacher


def test_school_allocation_never_exceeds_wallet_and_can_be_revoked():
    db = _session()
    school, _super_admin, school_admin, teacher = _fixtures(db)
    school_wallet = ai_credits.wallet_for_school(db, school.id)
    school_wallet.balance_credits = 500
    db.commit()

    allocation = ai_credits.grant_school_credits(db, school.id, teacher.id, 300, school_admin, "Cours IA")
    db.commit()
    assert school_wallet.balance_credits == 200
    assert ai_credits.wallet_for_user(db, teacher).balance_credits == 300
    assert allocation.remaining_credits == 300

    try:
        ai_credits.grant_school_credits(db, school.id, teacher.id, 300, school_admin)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
        db.rollback()
    else:
        raise AssertionError("Une école ne doit jamais distribuer plus que son solde")

    ai_credits.record_usage(db, teacher, "Aide", "Réponse", "ai_agent", "academic_help")
    db.commit()
    db.refresh(allocation)
    assert allocation.consumed_credits == 1
    assert allocation.remaining_credits == 299

    ai_credits.revoke_school_allocation(db, allocation, school_admin)
    db.commit()
    assert school_wallet.balance_credits == 499
    assert ai_credits.wallet_for_user(db, teacher).balance_credits == 0
    assert allocation.is_active is False


def test_manual_cash_payment_credits_target_user_and_tracks_validator():
    db = _session()
    _school, super_admin, _school_admin, teacher = _fixtures(db)
    pack = models.AICreditPack(
        name="Pack Cash",
        credits_amount=1500,
        price=7000,
        currency="FCFA",
        country_code="CI",
        region="africa",
        target_type="user",
        is_active=True,
    )
    db.add(pack)
    db.commit()

    payment = ai_billing.create_manual_ai_credit_payment(
        schemas.ManualAICreditPaymentRequest(
            owner_type="user",
            user_id=teacher.id,
            pack_id=pack.id,
            payment_method="cash",
            internal_reference="CAISSE-001",
        ),
        super_admin,
        db,
    )
    assert payment.status == "successful"
    assert payment.provider == "cash"
    assert payment.validated_by_id == super_admin.id
    assert ai_credits.wallet_for_user(db, teacher).balance_credits == 1500
    assert db.query(models.AICreditTransaction).filter(models.AICreditTransaction.payment_id == payment.id).count() == 1


def test_free_credit_requires_a_reason():
    db = _session()
    _school, super_admin, _school_admin, teacher = _fixtures(db)
    pack = models.AICreditPack(
        name="Pack Gratuit",
        credits_amount=100,
        price=0,
        target_type="user",
        is_active=True,
    )
    db.add(pack)
    db.commit()

    try:
        ai_billing.create_manual_ai_credit_payment(
            schemas.ManualAICreditPaymentRequest(
                owner_type="user",
                user_id=teacher.id,
                pack_id=pack.id,
                payment_method="free",
            ),
            super_admin,
            db,
        )
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("Une attribution gratuite sans motif doit être refusée")


def test_user_purchase_creates_manual_validation_request():
    db = _session()
    _school, _super_admin, _school_admin, teacher = _fixtures(db)
    pack = models.AICreditPack(
        name="Pack espèces",
        credits_amount=1500,
        price=7000,
        currency="FCFA",
        country_code="CI",
        region="africa",
        target_type="user",
        is_active=True,
    )
    db.add(pack)
    db.commit()

    result = ai_billing.my_ai_purchase(
        schemas.AICreditPurchaseRequest(pack_id=pack.id, provider="cash", note="Paiement à la caisse"),
        teacher,
        db,
    )

    assert result["status"] == "pending_manual_validation"
    assert result["provider"] == "cash"
    assert result["wallet_id"] == ai_credits.wallet_for_user(db, teacher).id
    assert ai_credits.wallet_for_user(db, teacher).balance_credits == 0

    validated = ai_billing.validate_manual_ai_payment(result["id"], _super_admin, db)
    assert validated.status == "successful"
    assert ai_credits.wallet_for_user(db, teacher).balance_credits == 1500


def test_online_purchase_returns_checkout_url(monkeypatch):
    db = _session()
    _school, _super_admin, _school_admin, teacher = _fixtures(db)
    pack = models.AICreditPack(
        name="Pack Stripe",
        credits_amount=4000,
        price=15000,
        currency="FCFA",
        country_code="CI",
        region="africa",
        target_type="user",
        is_active=True,
    )
    db.add(pack)
    db.commit()
    monkeypatch.setattr(
        payment_gateway,
        "create_checkout_session",
        lambda **_kwargs: payment_gateway.CheckoutSession(
            "https://checkout.example.test/ai",
            "provider-123",
            "redirect_required",
            {"ok": True},
        ),
    )

    result = ai_billing.my_ai_purchase(
        schemas.AICreditPurchaseRequest(
            pack_id=pack.id,
            provider="stripe",
            success_url="https://teducai.test/success",
            cancel_url="https://teducai.test/cancel",
        ),
        teacher,
        db,
    )

    assert result["checkout_url"] == "https://checkout.example.test/ai"
    assert result["provider_status"] == "redirect_required"
    assert result["provider_reference"] == "provider-123"
