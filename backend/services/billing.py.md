# billing.py
## Source File
- `backend/services/billing.py`
## Purpose
- Unifying layer for the enterprise Billing module. Aggregates the EXISTING money
  infrastructure (SchoolSubscription, AIWallet, PlatformPayment, AICreditTransaction,
  AuditLog) and manages the new billing config tables. Zero money-data duplication:
  invoices/transactions are PROJECTED from `PlatformPayment`, not stored again.
## Local Contracts
- `PLAN_CATALOG` mirrors `routers.system.SUBSCRIPTION_PRICES` plan keys (free/pro/max +
  custom) so upgrades route through the existing, tested `/system/subscription/change`.
- Functions: `overview`, `get/update_preferences`, `get/update_tax`,
  `get/update_auto_recharge`, `validate_promo`, `redeem_promo` (credits-type codes top
  up the school wallet + write an AICreditTransaction), `list_invoices`,
  `list_transactions`, `list_audit` (filters to billing action prefixes), `revenue_summary`.
- Every mutation records an audit row via `audit.record_audit` (action prefix `billing.`).
## Verification
- `python -m pytest backend/test_billing.py`
- Invoice PDF: `invoice_detail(db, school_id, payment_id)` assembles a full invoice (issuer=TeducAI, customer=school + tax profile, line items, subtotal/discount/tax-inclusive breakdown, total, status, QR reference); `render_invoice_pdf(detail)` renders a real PDF via reportlab (pure-Python, already in requirements). PLATFORM_ISSUER holds the vendor block.
- Payment methods (PCI-safe): `list/add/update/set_default/remove_payment_method` + `serialize_method` (adds expiry_state). `last4` sanitized to 4 digits; first method auto-default; setting a new default unsets others; removing the default promotes the newest remaining.
- AI billing assistant: `billing_assistant(db, school_id, user, question, language)` + `_assistant_context` assemble the school's REAL billing data (subscription, wallet, usage, this-vs-last-month spend, outstanding/failed counts, recent transactions, plan catalog) and call `ai_service.generate_response_from_config` grounded STRICTLY in that data; credit-gated (ensure_credits/record_usage). Empty question -> no AI call.
- Usage charts: `usage_timeseries(db, school_id, days)` returns per-day buckets (credits/tokens/requests/cost/spend) over a continuous window (pre-seeded days for a gap-free x-axis), a top-6 by-module credit breakdown, and totals. Bucketed in Python for SQLite/Postgres portability.
- Invoice e-mail: `email_invoice(db, school_id, payment_id, user, recipients=None)` renders the invoice PDF and sends it via services/email_service; recipients default to billing invoice_recipients + school e-mail; `_invoice_recipients` dedupes. Audited (billing.invoice.emailed).
