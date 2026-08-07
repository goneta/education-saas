# test_money_precision.py
## Source File
- `backend/test_money_precision.py`
## Purpose
- MONEY-02: proves the residue is real (`1.1 + 2.2 != 3.3`), that the helpers
  treat it as settled while 1 FCFA is still a real debt, and — the production
  scenario — that an invoice paid in two instalments now becomes **PAID**
  instead of staying PARTIAL (which blocked the pupil's certificate). Also
  checks that a genuine partial payment still reads PARTIAL and that a refund
  restores a coherent balance.
## Verification
- `python -m pytest backend/test_money_precision.py` (5 green).
