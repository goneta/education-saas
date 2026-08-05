# test_auth_hardening.py
## Source File
- `backend/test_auth_hardening.py`
## Purpose
- Lot 2 of the audit remediation. SEC-03: `security_middleware.client_ip`
  ignores `X-Forwarded-For` from an untrusted peer (rotating the header no
  longer buys a fresh rate-limit bucket) and honors it behind a declared proxy.
  SEC-05: a reset token is single-use, stored only as a hash, revokes sessions
  (`token_version`), unlocks the account, rejects unknown/expired tokens,
  invalidates sibling tokens, is throttled per hour, and enforces the password
  policy.
## Verification
- `python -m pytest backend/test_auth_hardening.py` (6 green).
