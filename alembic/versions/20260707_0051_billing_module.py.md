# 20260707_0051_billing_module.py
## Source File
- `alembic/versions/20260707_0051_billing_module.py`
## Purpose
- Creates the Billing config tables: billing_preferences, billing_tax_profiles,
  wallet_auto_recharges, billing_promo_codes, billing_promo_redemptions.
## Local Contracts
- New tables only (no ALTER of existing constraints), inline column FKs — safe on
  SQLite and Postgres. Idempotent: each table skipped if it already exists.
  down_revision = 20260705_0050. Verified: full chain `upgrade head` applies clean.
## Verification
- In-process `alembic command.upgrade(cfg, "head")` on a fresh SQLite DB creates all 5.
