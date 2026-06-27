from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import crypto_utils, database, models
from backend.scripts import sync_ai_credits
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
    def raise_for_status(self):
        return None

    def json(self):
        return {"data": {"total_credits": 80, "total_usage": 5}}


def test_cron_sync_updates_supported_and_skips_unsupported(monkeypatch):
    db = _session()
    db.add(models.AIProvider(
        name="OpenRouter", provider_type="openrouter",
        api_key_encrypted=crypto_utils.encrypt_secret("or-key"),
        available_credits=0, is_active=True, priority=10,
    ))
    db.add(models.AIProvider(name="OpenAI", provider_type="openai", available_credits=500, is_active=True, priority=11))
    db.add(models.AIProvider(name="Disabled OR", provider_type="openrouter", available_credits=0, is_active=False, priority=12))
    db.commit()

    monkeypatch.setattr(ai_credit_sync.httpx, "get", lambda *a, **k: _FakeResponse())
    summary = sync_ai_credits.run_sync(db)

    assert summary["total"] == 2  # disabled provider excluded
    assert summary["synced"] == 1
    statuses = {r["name"]: r["status"] for r in summary["results"]}
    assert statuses["OpenRouter"] == "synced"
    assert statuses["OpenAI"] == "unsupported"

    openrouter = db.query(models.AIProvider).filter(models.AIProvider.name == "OpenRouter").one()
    assert openrouter.available_credits == 75  # 80 - 5
    assert openrouter.credits_last_synced_at is not None
    # Cron run is audited.
    assert db.query(models.AuditLog).filter(models.AuditLog.action == "platform.ai_credits.cron_synced").count() == 1
