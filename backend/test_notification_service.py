from backend import models, schemas
from backend.services.notification_service import dispatch_notification


class _Response:
    status_code = 202
    text = "accepted"


def test_notification_without_provider_is_queued():
    payload = schemas.NotificationMessageCreate(channel=models.NotificationChannel.SMS, recipient="+2250000", message="Hello")
    status, response = dispatch_notification(None, payload)
    assert status == models.NotificationStatus.QUEUED
    assert "no active provider" in response


def test_notification_webhook_dispatch_is_sent(monkeypatch):
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return _Response()

    monkeypatch.setattr("backend.services.notification_service.httpx.post", fake_post)
    provider = models.NotificationProvider(
        channel=models.NotificationChannel.SMS,
        provider_name="https://sms.example.test/send",
        api_key_secret="secret",
        sender_id="SCHOOL",
        is_active=True,
        school_id=1,
    )
    payload = schemas.NotificationMessageCreate(channel=models.NotificationChannel.SMS, recipient="+2250000", message="Hello")

    status, response = dispatch_notification(provider, payload)

    assert status == models.NotificationStatus.SENT
    assert "accepted" in response
    assert calls[0]["headers"]["Authorization"] == "Bearer secret"
    assert calls[0]["json"]["sender_id"] == "SCHOOL"
