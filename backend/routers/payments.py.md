# payments.py

## Source File

- `backend/routers/payments.py`

## Purpose

- The centralized Payment Service API (`/payments`): provider list (`/providers`), signed idempotent provider webhooks (`/webhook/{provider}`), authorized manual reconciliation (`/{reference}/verify`), and payment status (`/{reference}`). Confirms `pending` `SchoolPayment` rows created by the checkout flow and updates the owning business module via `services/payment_service.py`.

## Local Contracts

- Webhooks verify a provider-specific or shared secret (`*_WEBHOOK_SECRET` / `SCHOOL_PAYMENT_WEBHOOK_SECRET`); skipped only when unset (dev), mirroring the platform webhook. Idempotent — a duplicate delivery for an already-successful payment is a no-op. Manual verify is restricted to manager/cashier/accountant roles and tenant-scoped. Real provider signature schemes (e.g. Stripe HMAC over the raw body) plug into `_verify_signature`.

## Verification

- `python -m pytest backend/test_payment_service.py`
- CinetPay endpoints: `POST /payments/cinetpay/notify` (public, form or JSON; optional x-token HMAC 403 on mismatch; ALWAYS re-verifies with /v2/payment/check before applying — replay/forgery safe; 503 when gateway unreachable so CinetPay retries; routes SCH- refs to apply_school_payment and TPL-/SUB- to apply_platform_payment; stores gateway payload in metadata_json.gateway_check) and `POST /payments/{reference}/refresh` (authenticated gateway-backed re-verify + idempotent apply; payer or same-school manager; 400 for non-CinetPay).
- `GET /providers` also returns `methods` — the user-facing mobile-money catalog (Orange Money/MTN Mobile Money/Moov Money/Wave -> provider cinetpay) so UIs render operator brands, never the gateway name. `GET /{reference}` includes `method` (user-facing label), `receipt_reference` and `receipt_verify_uuid`.
- `POST /{reference}/refund` (REFUND_ROLES = super-admin/school-admin/direction/accountant — NOT cashier; tenant-scoped; optional `{reason}`): records a verified refund through `payment_service.refund_school_payment` — idempotent (already refunded => applied False), 409 for never-successful payments. The money return itself is executed at the provider.
