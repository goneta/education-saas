# test_webhook_auth.py
## Source File
- `backend/test_webhook_auth.py`
## Purpose
- Lot 0 of the pre-production audit remediation. SEC-01: unconfigured secret in
  production -> 503 (never a silent pass), tolerated outside production, exact
  value required otherwise (empty/prefix/case/whitespace variants all 403),
  provider-specific secret wins over the shared one. Endpoint-level proof that a
  forged school-payment confirmation leaves the payment `pending` (no money
  applied). SEC-01 also checked on the platform helper. CFG-01: production
  refuses a missing `DATABASE_URL` and a SQLite URL, accepts PostgreSQL, and
  leaves development untouched.
## Verification
- `python -m pytest backend/test_webhook_auth.py` (7 green).
