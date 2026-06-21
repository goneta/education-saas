# 20260621_0019_cash_ai_credit_management.py

## Purpose

- Adds traceable cash payment fields to school fee payments.
- Adds AI credit pack beneficiary targeting and manual validation metadata.
- Adds school-to-user AI credit allocations with remaining, consumed, and revocation tracking.

## Production Contract

- Apply after `20260612_0018` with `python -m alembic upgrade head`.
- Operations are existence-aware so production databases with partially applied columns can recover safely.

## Verification

- `python -m alembic heads`
- `python -m alembic upgrade head`
