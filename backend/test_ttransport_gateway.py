"""TTransportAI gateway placeholder: honest status, never a fake connection."""

from backend.services import ttransport_gateway


def test_status_unconfigured(monkeypatch):
    monkeypatch.delenv("TTRANSPORTAI_API_URL", raising=False)
    monkeypatch.delenv("TTRANSPORTAI_API_KEY", raising=False)
    status = ttransport_gateway.integration_status()
    assert status["connected"] is False
    assert status["configured"] is False
    assert len(status["capabilities"]) == 11
    assert "à venir" in status["message"].lower()


def test_status_configured_but_never_connected(monkeypatch):
    """Credentials alone must NOT report a connection — no client exists yet."""
    monkeypatch.setenv("TTRANSPORTAI_API_URL", "https://api.ttransportai.example")
    monkeypatch.setenv("TTRANSPORTAI_API_KEY", "k")
    status = ttransport_gateway.integration_status()
    assert status["configured"] is True
    assert status["connected"] is False
