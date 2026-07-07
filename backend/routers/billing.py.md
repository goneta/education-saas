# billing.py
## Source File
- `backend/routers/billing.py`
## Purpose
- Unified `/billing` API for the enterprise Billing page. One surface over existing
  money infra: the Subscription tab drives `/system/subscription/*`; credit purchases
  drive `/ai_billing`; this router adds overview aggregation, billing config
  (preferences/tax/auto-recharge), promo codes, and projected invoice/transaction/
  audit/revenue views.
## Local Contracts
- Management (`/overview`, `/plans`, preferences, tax, auto-recharge, promos, invoices,
  transactions, usage, audit) limited to admin/direction/accountant (`_MANAGE_ROLES`).
- Revenue analytics (`/admin/revenue`) and promo-code authoring (`/admin/promos`) are
  Super-Admin only. Super Admin must pass `school_id`; others are school-scoped by token.
- Delegates all logic to `services/billing.py`; every write commits + audits.
## Verification
- `python -m pytest backend/test_billing.py`
- Invoice PDF endpoints: `GET /billing/invoices/{payment_id}` (JSON detail, 404 if not this school's) and `GET /billing/invoices/{payment_id}/pdf` (Streaminged `application/pdf`, Content-Disposition attachment). Management-role + school-scoped like the rest.
- Payment-method CRUD: `GET/POST /billing/payment-methods`, `PATCH/DELETE /billing/payment-methods/{id}`, `POST /billing/payment-methods/{id}/default`. Management-role + school-scoped; every mutation audited (billing.payment_method.*).
- AI assistant: `POST /billing/assistant` {question, language?} -> {answer, context_summary}. Management-role + school-scoped, credit-gated on the caller's AI wallet.
- Usage charts: `GET /billing/usage/timeseries?days=` -> {days, series, by_module, totals}. Management-role + school-scoped; days clamped to 1-365.
