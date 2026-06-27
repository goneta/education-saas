from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import crypto_utils, database, models
from backend.services import ai_provider_bootstrap


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_bootstrap_creates_providers_from_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gem-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    monkeypatch.delenv("MANUS_API_KEY", raising=False)
    db = _session()
    result = ai_provider_bootstrap.bootstrap_providers_from_env(db)
    assert result["created"] == 2
    rows = {r.provider_type: r for r in db.query(models.AIProvider).all()}
    assert set(rows) == {"openrouter", "gemini"}
    # Keys stored encrypted, env label set, base url from defaults.
    assert crypto_utils.decrypt_secret(rows["openrouter"].api_key_encrypted) == "or-key"
    assert rows["openrouter"].account_label == "env"
    assert rows["gemini"].base_url.startswith("https://generativelanguage.googleapis.com")


def test_bootstrap_is_idempotent_and_refreshes_env_rows(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key-1")
    for var in ("OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "GROK_API_KEY", "MANUS_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    db = _session()
    ai_provider_bootstrap.bootstrap_providers_from_env(db)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key-2")
    result = ai_provider_bootstrap.bootstrap_providers_from_env(db)
    assert result["created"] == 0 and result["updated"] == 1
    rows = db.query(models.AIProvider).filter(models.AIProvider.provider_type == "openrouter").all()
    assert len(rows) == 1  # no duplicate
    assert crypto_utils.decrypt_secret(rows[0].api_key_encrypted) == "or-key-2"


def test_bootstrap_does_not_touch_ui_created_providers(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    for var in ("OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "GROK_API_KEY", "MANUS_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    db = _session()
    ui_row = models.AIProvider(
        name="UI OpenRouter", provider_type="openrouter",
        api_key_encrypted=crypto_utils.encrypt_secret("ui-key"),
        account_label="ui", is_active=True,
    )
    db.add(ui_row)
    db.commit()
    ai_provider_bootstrap.bootstrap_providers_from_env(db)
    # UI row untouched; a separate env row was created.
    ui_after = db.query(models.AIProvider).filter(models.AIProvider.account_label == "ui").one()
    assert crypto_utils.decrypt_secret(ui_after.api_key_encrypted) == "ui-key"
    assert db.query(models.AIProvider).filter(models.AIProvider.account_label == "env").count() == 1


def test_env_api_key_for_supports_aliases(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.setenv("GROK_API_KEY", "grok-key")
    assert ai_provider_bootstrap.env_api_key_for("grok") == "grok-key"
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    assert ai_provider_bootstrap.env_api_key_for("grok") is None
