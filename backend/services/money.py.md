# money.py
## Source File
- `backend/services/money.py`
## Purpose
- MONEY-02 mitigation WITHOUT a schema migration. Amounts are stored as `FLOAT`,
  so `1.1 + 2.2 == 3.3000000000000003`: an invoice paid in full kept a 1e-16
  residue, stayed `PARTIAL` forever and — through `routers/students.py` —
  **blocked the pupil's certificate** although the family had paid everything.
- `normalize(v)` rounds a computed amount before it is stored (residue never
  accumulates in the database); `is_settled(b)` / `is_outstanding(b)` compare
  against `EPSILON` (0.005 = half a cent) instead of zero; `remaining(due, paid)`
  returns a normalized, non-negative balance.
## Local Contracts
- NEVER compare a money column to zero directly (`balance <= 0`, `amount > 0`):
  use these helpers. EPSILON is deliberately far below the smallest real amount
  (1 FCFA) and far above any float residue, so a real debt is never hidden.
- Consumers: `services/payment_service.py` (payment + refund invoice status),
  `routers/students.py` (outstanding balance, certificate blocking).
- The definitive fix remains migrating the money columns to `Numeric`; this
  module makes that migration non-urgent, not unnecessary.
## Verification
- `python -m pytest backend/test_money_precision.py` (5 green).
