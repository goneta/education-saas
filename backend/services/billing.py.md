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
