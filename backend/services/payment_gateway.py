from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx


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
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][unit_amount]": str(max(1, round(amount * 100))),
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
        "channels": "MOBILE_MONEY",
        "metadata": reference,
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
