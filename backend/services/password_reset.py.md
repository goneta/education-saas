# password_reset.py
## Source File
- `backend/services/password_reset.py`
## Purpose
- Self-service password reset (audit SEC-05): before this, a forgotten password
  could only be fixed by an administrator - untenable at the start of a school
  year. `create_token` (throttled, PASSWORD_RESET_MAX_PER_HOUR), `send_reset_email`
  (FR/EN, link = APP_URL/reset-password?token=...), `consume_token` (one shot:
  marks the token used AND invalidates the user's other pending tokens; rejects
  unknown/used/expired), `apply_new_password` (policy enforced, account unlocked,
  `token_version` bumped so every JWT issued before the reset dies).
## Local Contracts
- Only the SHA-256 hash of the token is stored - the database never holds a
  usable reset link. TTL: PASSWORD_RESET_TTL_MINUTES (default 60).
- Callers must never reveal whether an address exists (see routers/auth.py:
  the answer is always generic) and must never fake a send: when SMTP is not
  configured the endpoint answers 503.
## Verification
- `python -m pytest backend/test_auth_hardening.py` (6 green).
