"""Privacy-conscious Sentry initialization for the FastAPI process."""

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def _sample_rate(name: str, default: float) -> float:
    value = float(os.getenv(name, str(default)))
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


def _scrub_event(event: dict, _hint: dict) -> dict:
    for key in ("request", "user", "contexts", "extra", "breadcrumbs", "tags",
                "logentry", "fingerprint", "transaction"):
        event.pop(key, None)
    if event.get("message") != "teducai.sentry.smoke":
        event.pop("message", None)
    for error in event.get("exception", {}).get("values", []):
        error["value"] = error.get("type", "ApplicationError")
        for frame in error.get("stacktrace", {}).get("frames", []):
            frame.pop("vars", None)
            frame.pop("pre_context", None)
            frame.pop("post_context", None)
            frame.pop("context_line", None)
    return event


def _scrub_transaction(event: dict, hint: dict) -> dict:
    route = event.get("transaction") if event.get("transaction_info", {}).get("source") == "route" else None
    _scrub_event(event, hint)
    if route:
        event["transaction"] = route
    for span in event.get("spans", []):
        span.pop("description", None)
        span.pop("data", None)
        span.pop("tags", None)
    return event


def _scrub_log(log: dict, _hint: dict) -> dict:
    attributes = log.get("attributes", {})
    logger_name = attributes.get("logger.name", "application")
    log["body"] = f"{log.get('severity_text', 'WARNING')} from {logger_name}"
    log["attributes"] = {
        key: attributes[key]
        for key in ("logger.name", "code.file.path", "code.line.number")
        if key in attributes
    }
    return log


def configure_sentry() -> bool:
    """Enable Sentry when a DSN is present; otherwise leave local runs untouched."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("APP_ENV", "development"),
        release=os.getenv("SENTRY_RELEASE") or None,
        send_default_pii=False,
        max_request_body_size="never",
        include_local_variables=False,
        include_source_context=False,
        auto_enabling_integrations=False,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=None, event_level=None,
                               sentry_logs_level=logging.WARNING, capture_sentry_logs=True),
        ],
        enable_logs=True,
        traces_sample_rate=_sample_rate("SENTRY_TRACES_SAMPLE_RATE", 0.1),
        profile_session_sample_rate=_sample_rate("SENTRY_PROFILES_SAMPLE_RATE", 0.01),
        profile_lifecycle="trace",
        before_send=_scrub_event,
        before_send_transaction=_scrub_transaction,
        before_send_log=_scrub_log,
        before_breadcrumb=lambda _breadcrumb, _hint: None,
    )
    return True
