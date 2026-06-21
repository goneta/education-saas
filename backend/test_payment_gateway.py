from backend.services import payment_gateway


class FakeResponse:
    status_code = 200
    text = ""

    def json(self):
        return {"id": "cs_test_123", "url": "https://checkout.example.test/session"}


def test_stripe_checkout_reports_missing_configuration(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    session = payment_gateway.create_checkout_session(
        provider="stripe",
        reference="TPL-TEST",
        amount=7000,
        currency="XOF",
        title="Credits IA",
        success_url="https://teducai.test/success",
        cancel_url="https://teducai.test/cancel",
    )

    assert session.status == "pending_configuration"
    assert session.checkout_url is None


def test_stripe_checkout_returns_provider_redirect(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
    monkeypatch.setattr(payment_gateway.httpx, "post", lambda *args, **kwargs: FakeResponse())

    session = payment_gateway.create_checkout_session(
        provider="stripe",
        reference="TPL-TEST",
        amount=7000,
        currency="XOF",
        title="Credits IA",
        success_url="https://teducai.test/success",
        cancel_url="https://teducai.test/cancel",
    )

    assert session.status == "redirect_required"
    assert session.provider_reference == "cs_test_123"
    assert session.checkout_url == "https://checkout.example.test/session"
