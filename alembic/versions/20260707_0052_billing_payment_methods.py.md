# 20260707_0052_billing_payment_methods.py
## Source File
- `alembic/versions/20260707_0052_billing_payment_methods.py`
## Purpose
- Creates `billing_payment_methods` (saved payment methods per school).
## Local Contracts
- New table only, inline column FKs, idempotent (skipped if it exists).
  PCI-safe columns only: brand/last4/expiry + optional gateway_token (no PAN/CVV).
  down_revision = 20260707_0051.
## Verification
- In-process `alembic upgrade head` on a fresh SQLite DB creates the table.
