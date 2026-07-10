from __future__ import annotations

import hashlib
import hmac
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger("teducai.payment_gateway")


@dataclass
class CheckoutSession:
    checkout_url: Optional[str]
    provider_reference: Optional[str]
    status: str
    provider_payload: dict[str, Any]


def _response_json(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
        return payload if isinstance(payload, dict) else {"data": payload}
    except ValueError:
        return {"response": response.text[:500]}


def _stripe_checkout(
    reference: str,
    amount: float,
    currency: str,
    title: str,
    success_url: str,
    cancel_url: str,
    api_key: Optional[str] = None,
) -> CheckoutSession:
    secret = api_key or os.getenv("STRIPE_SECRET_KEY", "")
    if not secret:
        return CheckoutSession(None, None, "pending_configuration", {"message": "Stripe credentials are not configured"})
    stripe_currency = "xof" if currency.upper() == "FCFA" else currency.lower()
    unit_multiplier = 1 if stripe_currency in {"xof"} else 100
    response = httpx.post(
        "https://api.stripe.com/v1/checkout/sessions",
        headers={"Authorization": f"Bearer {secret}"},
        data={
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": reference,
            "metadata[teducai_reference]": reference,
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": stripe_currency,
            "line_items[0][price_data][unit_amount]": str(max(1, round(amount * unit_multiplier))),
            "line_items[0][price_data][product_data][name]": title[:120],
        },
        timeout=20,
    )
    payload = _response_json(response)
    if response.status_code >= 400:
        return CheckoutSession(None, None, "failed", payload)
    return CheckoutSession(payload.get("url"), payload.get("id"), "redirect_required", payload)


def _cinetpay_checkout(
    reference: str,
    amount: float,
    currency: str,
    title: str,
    success_url: str,
    cancel_url: str,
    network: Optional[str],
    api_key: Optional[str] = None,
    site_id: Optional[str] = None,
) -> CheckoutSession:
    token = api_key or os.getenv("CINETPAY_API_KEY", "")
    merchant = site_id or os.getenv("CINETPAY_SITE_ID", "")
    endpoint = os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com/v2/payment")
    if not token or not merchant:
        return CheckoutSession(None, None, "pending_configuration", {"message": "CinetPay credentials are not configured"})
    notify_url = os.getenv("CINETPAY_NOTIFY_URL", "")
    # Channels are dynamically configurable: ALL (default) exposes every method
    # CinetPay enables on the merchant account (Orange, MTN, Moov, Wave, cards…);
    # narrower values: MOBILE_MONEY, CREDIT_CARD, WALLET.
    channels = os.getenv("CINETPAY_CHANNELS", "ALL")
    payload = {
        "apikey": token,
        "site_id": merchant,
        "transaction_id": reference,
        "amount": max(5, round(amount)),
        "currency": "XOF" if currency.upper() == "FCFA" else currency.upper(),
        "description": title[:180],
        "return_url": success_url,
        "cancel_url": cancel_url,
        "notify_url": notify_url,
        "channels": channels,
        "metadata": reference,
        # Card payments require a customer block; CinetPay ignores it for
        # mobile money, so generic values keep every channel available.
        "customer_name": "TeducAI",
        "customer_surname": "Client",
    }
    if network:
        payload["payment_method"] = network
    response = httpx.post(endpoint, json=payload, timeout=20)
    response_payload = _response_json(response)
    if response.status_code >= 400:
        return CheckoutSession(None, None, "failed", response_payload)
    data = response_payload.get("data") if isinstance(response_payload.get("data"), dict) else response_payload
    return CheckoutSession(
        data.get("payment_url") or data.get("url"),
        data.get("payment_token") or data.get("transaction_id") or reference,
        "redirect_required",
        response_payload,
    )


def _djamo_checkout(
    reference: str,
    amount: float,
    currency: str,
    title: str,
    success_url: str,
    cancel_url: str,
    api_key: Optional[str] = None,
) -> CheckoutSession:
    endpoint = os.getenv("DJAMO_PAYMENT_URL", "")
    token = api_key or os.getenv("DJAMO_API_KEY", "")
    if not endpoint or not token:
        return CheckoutSession(None, None, "pending_configuration", {"message": "Djamo credentials or payment endpoint are not configured"})
    response = httpx.post(
        endpoint,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "reference": reference,
            "amount": amount,
            "currency": currency,
            "description": title,
            "success_url": success_url,
            "cancel_url": cancel_url,
        },
        timeout=20,
    )
    payload = _response_json(response)
    if response.status_code >= 400:
        return CheckoutSession(None, None, "failed", payload)
    return CheckoutSession(
        payload.get("checkout_url") or payload.get("payment_url") or payload.get("url"),
        payload.get("id") or payload.get("reference") or reference,
        "redirect_required",
        payload,
    )


# --- CinetPay server-side verification & webhook authenticity -----------------
# CinetPay's integration contract: NEVER trust the notify callback body alone.
# The authoritative source of truth is POST /v2/payment/check — every status
# transition must be confirmed there before money-side effects run. This also
# neutralises forged/replayed notifications even when no HMAC secret is set.

CINETPAY_STATUS_MAP = {
    "ACCEPTED": "successful",
    "REFUSED": "failed",
    "CANCELLED": "failed",
    "WAITING_FOR_CUSTOMER": "pending",
    "PENDING": "pending",
}

# Field order defined by CinetPay for the x-token HMAC over the notify form.
CINETPAY_HMAC_FIELDS = (
    "cpm_site_id", "cpm_trans_id", "cpm_trans_date", "cpm_amount", "cpm_currency",
    "signature", "payment_method", "cel_phone_num", "cpm_phone_prefixe",
    "cpm_language", "cpm_version", "cpm_payment_config", "cpm_page_action",
    "cpm_custom", "cpm_designation", "cpm_error_message",
)


def cinetpay_check_transaction(reference: str) -> tuple[str, dict[str, Any]]:
    """Verify a transaction directly with CinetPay (`/v2/payment/check`).

    Returns ``(status, payload)`` where status is one of
    successful / failed / pending / unknown. ``unknown`` means the gateway
    could not be reached or credentials are missing — callers must NOT apply
    any state change on ``unknown``.
    """
    token = os.getenv("CINETPAY_API_KEY", "")
    merchant = os.getenv("CINETPAY_SITE_ID", "")
    if not token or not merchant:
        return "unknown", {"message": "CinetPay credentials are not configured"}
    endpoint = os.getenv(
        "CINETPAY_CHECK_URL",
        os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com/v2/payment").rstrip("/") + "/check",
    )
    try:
        response = httpx.post(
            endpoint,
            json={"apikey": token, "site_id": merchant, "transaction_id": reference},
            timeout=20,
        )
    except httpx.HTTPError as exc:
        logger.warning("CinetPay check unreachable for %s: %s", reference, exc)
        return "unknown", {"message": f"gateway unreachable: {exc.__class__.__name__}"}
    payload = _response_json(response)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    raw_status = str((data or {}).get("status") or "").upper()
    code = str(payload.get("code") or "")
    if raw_status in CINETPAY_STATUS_MAP:
        return CINETPAY_STATUS_MAP[raw_status], payload
    if code == "600" or response.status_code >= 500:
        return "unknown", payload
    # 662 = WAITING_CUSTOMER_TO_VALIDATE, 623/627 style codes = not found/failed.
    if code in {"662", "623"}:
        return "pending", payload
    logger.info("CinetPay check for %s returned code=%s status=%s", reference, code, raw_status or "-")
    return "unknown", payload


def verify_cinetpay_token(x_token: Optional[str], form: dict[str, Any]) -> bool:
    """Validate the `x-token` HMAC (SHA-256) CinetPay sends with each notify.

    Returns True when the token matches, or when no CINETPAY_SECRET_KEY is
    configured (the check API remains the authoritative gate either way).
    Returns False on mismatch — callers must reject with 403.
    """
    secret = os.getenv("CINETPAY_SECRET_KEY", "")
    if not secret:
        return True  # not configured: rely on cinetpay_check_transaction
    if not x_token:
        return False
    data = "".join(str(form.get(field, "") or "") for field in CINETPAY_HMAC_FIELDS)
    expected = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, x_token.strip())


def create_checkout_session(
    provider: str,
    reference: str,
    amount: float,
    currency: str,
    title: str,
    success_url: Optional[str],
    cancel_url: Optional[str],
    mobile_money_network: Optional[str] = None,
    api_key: Optional[str] = None,
    merchant_id: Optional[str] = None,
) -> CheckoutSession:
    success = success_url or os.getenv("APP_URL", "http://localhost:3000")
    cancel = cancel_url or success
    if provider == "stripe":
        return _stripe_checkout(reference, amount, currency, title, success, cancel, api_key)
    if provider == "cinetpay":
        return _cinetpay_checkout(reference, amount, currency, title, success, cancel, mobile_money_network, api_key, merchant_id)
    if provider == "djamo":
        return _djamo_checkout(reference, amount, currency, title, success, cancel, api_key)
    return CheckoutSession(None, reference, "pending", {"message": "Manual payment selected"})
