from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import crypto_utils, database, models
from backend.routers import ai_billing
from backend.services import ai_credit_sync


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_balance_api_support_matches_provider_reality():
    assert ai_credit_sync.balance_api_supported("openrouter") is True
    for unsupported in ("openai", "anthropic", "claude", "gemini", "grok", "xai", "manus"):
        assert ai_credit_sync.balance_api_supported(unsupported) is False


def test_sync_openrouter_updates_balance(monkeypatch):
    provider = models.AIProvider(
        name="OpenRouter",
        provider_type="openrouter",
        api_key_encrypted=crypto_utils.encrypt_secret("sk-test"),
        available_credits=0,
    )
    monkeypatch.setattr(
        ai_credit_sync.httpx,
        "get",
        lambda *a, **k: _FakeResponse({"data": {"total_credits": 100, "total_usage": 30}}),
    )
    result = ai_credit_sync.sync_provider_credits(provider)
    assert result["status"] == "synced"
    assert result["available_credits"] == 70
    ai_credit_sync.apply_sync_result(provider, result)
    assert provider.available_credits == 70
    assert provider.credits_last_synced_at is not None


def test_sync_unsupported_provider_keeps_value():
    provider = models.AIProvider(name="OpenAI", provider_type="openai", available_credits=500)
    result = ai_credit_sync.sync_provider_credits(provider)
    assert result["status"] == "unsupported"
    ai_credit_sync.apply_sync_result(provider, result)
    assert provider.available_credits == 500  # unchanged


def test_sync_supported_provider_without_key_reports_no_key():
    provider = models.AIProvider(name="OpenRouter", provider_type="openrouter", available_credits=0)
    result = ai_credit_sync.sync_provider_credits(provider)
    assert result["status"] == "no_key"


def test_monitoring_totals_reflect_provider_credits_and_purchases():
    db = _session()
    super_admin = models.User(email="sa@test.local", hashed_password="x", full_name="SA", role=models.UserRole.SUPER_ADMIN, is_active=True)
    db.add(super_admin)
    db.add(models.AIProvider(name="P1", provider_type="openrouter", available_credits=1000, is_active=True))
    db.add(models.AIProvider(name="P2", provider_type="openai", available_credits=500, is_active=True))
    db.add(models.PlatformPayment(
        reference="TPL-TEST-1", payment_type="ai_credit_purchase", amount=3000, currency="XOF",
        provider="cash", status="successful", beneficiary_entity="school", credits_amount=200,
    ))
    db.commit()

    monitoring = ai_billing.platform_ai_monitoring(current_user=super_admin, db=db)
    assert monitoring["total_provider_credits"] == 1500
    assert monitoring["total_credits_purchased"] == 200
    # Global pool decreases by what was purchased.
    assert monitoring["remaining_system_credits"] == 1300
