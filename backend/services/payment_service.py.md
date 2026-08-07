# payment_service.py

## Source File

- `backend/services/payment_service.py`

## Purpose

- Centralized confirmation + per-institution gateway config for school-side payments. `apply_school_payment` idempotently transitions a `SchoolPayment` to successful, updating the owning `StudentInvoice` balance/status, writing an audit record and notifying the payer — exactly once. `enabled_providers` lists the providers an institution has switched on (active `SchoolPaymentAccount`) plus cash.

## Local Contracts

- No module may re-implement payment confirmation; call `apply_school_payment`. The success side-effects run only on the first transition to "successful" (replays are safe no-ops → no double-credit). Tenant scope is enforced by the caller (router) and by matching `school_id` when loading the invoice.

## Verification

- `python -m pytest backend/test_payment_service.py`
- `apply_platform_payment(db, payment, status=..., provider_reference=..., extra_metadata=...)`: the single idempotent confirmation path for PlatformPayment (credit purchases -> ai_credits.apply_platform_payment_success; subscriptions -> activation + School flags). Shared by the legacy platform webhook and the CinetPay notify endpoint; never downgrades a confirmed payment.
- User-facing methods: `MOBILE_MONEY_METHODS` (orange_money/mtn_money/moov_money/wave -> provider "cinetpay") and `user_facing_method(provider, network)` — UIs and receipts show the operator brand (Orange Money, MTN Mobile Money, Moov Money, Wave) or a neutral family label, NEVER a gateway name.
- Automatic receipts: `generate_school_payment_receipt(db, payment)` runs on the first successful `apply_school_payment` — one `GeneratedDocument` (RECEIPT, REC-…, source_type="school_payment"/source_id=payment.id => idempotent on replay) + a `DocumentRegistry` record (QR-verifiable at /verify/{uuid}); receipt_reference/receipt_verify_uuid stored on payment.metadata_json.
- Refunds: `refund_school_payment(db, payment, current_user=…, reason=…)` — successful -> refunded exactly once (already refunded => False; never-successful => ValueError). Reverses the invoice balance/status, revokes the registry receipt, audits `school.payment.refunded`, notifies the student. Records the reversal in the school's books; the money return itself is executed at the provider (panel/cash drawer), never via the checkout API.
- MONEY-02: le statut de facture est calcule avec `services/money` (normalisation a l ecriture, comparaison avec tolerance) au lieu de `remaining_balance <= 0` sur des flottants — une facture soldee restait PARTIAL a cause d un residu de 1e-16.
