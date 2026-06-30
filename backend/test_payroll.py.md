# test_payroll.py
## Purpose
- #7 Payroll: engine breakdown correctness, base-amount-by-pay-type, generate+self-service+duplicate-period 409, pay marks paid with method, RBAC (non-admin 403 / owner reads own).
## Verification
- `python -m pytest backend/test_payroll.py`
