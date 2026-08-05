# webhook_auth.py
## Source File
- `backend/webhook_auth.py`
## Purpose
- Shared-secret authentication for inbound provider webhooks, **fail-closed**
  (audit SEC-01). `verify_shared_secret(provided, *env_names, purpose=...)`:
  resolves the first configured secret among `env_names`; if none is configured
  it raises **503** in production (the provider retries once the host is fixed,
  and NO money side-effect runs) and degrades to a no-op outside production;
  on mismatch it raises **403** using a constant-time comparison.
## Local Contracts
- Every public webhook endpoint MUST go through this module — never re-implement
  `if secret and provided != secret`, which accepted anonymous callers whenever
  the environment variable was absent.
- Production is detected by `database.is_production()` (APP_ENV=production OR a
  `.env.production` file present) — one rule shared with the SECRET_KEY and
  DATABASE_URL guards.
- Consumers: `routers/payments.py::_verify_signature` (provider-specific secret
  then `SCHOOL_PAYMENT_WEBHOOK_SECRET`), `routers/ai_billing.py::_verify_webhook`
  (`PLATFORM_PAYMENT_WEBHOOK_SECRET` / `SCHOOL_PAYMENT_WEBHOOK_SECRET`).
## Verification
- `python -m pytest backend/test_webhook_auth.py` (7 green).
