# payment_service.py

## Source File

- `backend/services/payment_service.py`

## Purpose

- Centralized confirmation + per-institution gateway config for school-side payments. `apply_school_payment` idempotently transitions a `SchoolPayment` to successful, updating the owning `StudentInvoice` balance/status, writing an audit record and notifying the payer — exactly once. `enabled_providers` lists the providers an institution has switched on (active `SchoolPaymentAccount`) plus cash.

## Local Contracts

- No module may re-implement payment confirmation; call `apply_school_payment`. The success side-effects run only on the first transition to "successful" (replays are safe no-ops → no double-credit). Tenant scope is enforced by the caller (router) and by matching `school_id` when loading the invoice.

## Verification

- `python -m pytest backend/test_payment_service.py`
