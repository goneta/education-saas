# test_billing.py
## Source File
- `backend/test_billing.py`
## Purpose
- Covers the billing service + router: overview aggregation (subscription + wallet +
  usage), preferences/tax/auto-recharge upsert-with-default, promo validate + redeem
  (credits grant tops up wallet; per-school-limit blocks re-use; percent-discount
  preview), invoices/transactions projection from PlatformPayment (+ status filter),
  RBAC gating (teacher 403; non-super-admin blocked from revenue), and super-admin
  revenue summary + promo-code CRUD (409 on duplicate).
## Verification
- `python -m pytest backend/test_billing.py` (10 tests, all green).
- Invoice PDF test: `test_invoice_detail_and_pdf` verifies detail assembly (tax-inclusive breakdown, customer tax id), a valid %PDF response with attachment filename, and 404 for unknown/cross-school invoices.
