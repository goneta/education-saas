# test_cash_ai_credits.py

## Purpose

- Verifies school-to-user AI credit distribution and revocation.
- Verifies Super Admin cash validation credits the intended wallet exactly once.
- Verifies free AI credit grants require an audit reason.
- Verifies cash purchases remain pending until Super Admin validation and that credits are then applied exactly once.
- Verifies configured online purchases return the provider checkout URL and reference without prematurely crediting the wallet.

## Verification

- `python -m pytest backend/test_cash_ai_credits.py`
