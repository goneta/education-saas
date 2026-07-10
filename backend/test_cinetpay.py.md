# test_cinetpay.py
## Source File
- `backend/test_cinetpay.py`
## Purpose
- HMAC x-token verification (good/forged/missing/no-secret); notify verifies with the check
  API then applies idempotently (invoice PAID once, replay = no-op but re-verified); forged
  token 403 without touching the gateway; body status never trusted (check REFUSED wins);
  gateway unreachable -> 503 (CinetPay retry); platform subscription activation via the shared
  applier; /refresh gateway-backed (cashier ok, cross-school 403, non-cinetpay 400); status
  mapping ACCEPTED/REFUSED/WAITING + network failure -> unknown.
## Verification
- `python -m pytest backend/test_cinetpay.py` (8 green).
