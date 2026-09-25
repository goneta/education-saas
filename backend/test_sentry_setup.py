"""Sentry must remain optional and must not export student or payment details."""

import pytest

from backend import sentry_setup


def test_missing_dsn_does_not_initialize(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.setattr(sentry_setup.sentry_sdk, "init", lambda **_kwargs: pytest.fail("unexpected init"))
    assert sentry_setup.configure_sentry() is False


def test_configured_dsn_uses_private_sampling(monkeypatch):
    captured = {}
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.invalid/1")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(sentry_setup.sentry_sdk, "init", lambda **kwargs: captured.update(kwargs))
    assert sentry_setup.configure_sentry() is True
    assert captured["send_default_pii"] is False
    assert captured["max_request_body_size"] == "never"
    assert captured["include_local_variables"] is False
    assert captured["auto_enabling_integrations"] is False
    assert captured["enable_logs"] is True
    assert captured["traces_sample_rate"] == 0.1
    assert captured["profile_session_sample_rate"] == 0.01
    assert captured["environment"] == "production"


@pytest.mark.parametrize("bad", ["-0.1", "1.1", "unknown"])
def test_invalid_sample_rate_fails_configuration(monkeypatch, bad):
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", bad)
    with pytest.raises(ValueError):
        sentry_setup._sample_rate("SENTRY_TRACES_SAMPLE_RATE", 0.1)


def test_error_event_strips_request_identity_and_exception_values():
    event = {
        "request": {"headers": {"Authorization": "Bearer secret"}, "data": "child record"},
        "user": {"email": "student@example.test"},
        "extra": {"payment": "private"},
        "breadcrumbs": [{"message": "private"}],
        "tags": {"school": "private"},
        "exception": {"values": [{
            "type": "ValueError", "value": "child record",
            "stacktrace": {"frames": [{"filename": "grades.py", "lineno": 12,
                                       "vars": {"student": "private"},
                                       "context_line": "child record"}]},
        }]},
    }
    clean = sentry_setup._scrub_event(event, {})
    assert set(clean) == {"exception"}
    error = clean["exception"]["values"][0]
    assert error["value"] == "ValueError"
    assert error["stacktrace"]["frames"] == [{"filename": "grades.py", "lineno": 12}]


def test_trace_spans_drop_sql_and_parameters():
    event = {"request": {"url": "/student/123"},
             "spans": [{"op": "db", "description": "SELECT * FROM pupils WHERE name='child'",
                        "data": {"parameters": "private"}, "tags": {"school": "private"}}]}
    clean = sentry_setup._scrub_transaction(event, {})
    assert clean == {"spans": [{"op": "db"}]}


def test_trace_keeps_route_template_but_not_raw_user_url():
    route_event = {"transaction": "GET /students/{student_id}",
                   "transaction_info": {"source": "route"}}
    raw_event = {"transaction": "GET /students/123?token=private",
                 "transaction_info": {"source": "url"}}
    assert sentry_setup._scrub_transaction(route_event, {})["transaction"] == "GET /students/{student_id}"
    assert "transaction" not in sentry_setup._scrub_transaction(raw_event, {})


def test_log_keeps_severity_and_source_without_message_parameters():
    log = {"severity_text": "ERROR", "body": "Student Awa owes 5000",
           "attributes": {"logger.name": "teducai.finance", "code.line.number": 42,
                          "sentry.message.parameter.0": "Awa", "school_id": 9}}
    clean = sentry_setup._scrub_log(log, {})
    assert clean["body"] == "ERROR from teducai.finance"
    assert clean["attributes"] == {"logger.name": "teducai.finance", "code.line.number": 42}


def test_safe_smoke_message_survives_without_other_messages():
    assert sentry_setup._scrub_event({"message": "teducai.sentry.smoke"}, {})["message"] == "teducai.sentry.smoke"
    assert sentry_setup._scrub_event({"message": "student@example.test"}, {}) == {}
