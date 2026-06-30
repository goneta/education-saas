# payroll.py
## Source File
- `backend/routers/payroll.py`
## Purpose
- Real payroll system under Finance (#7), prefix `/finance/payroll`. Per-employee `SalaryProfile` CRUD + payslip generation through the country-extensible engine (`services/payroll.py`), with itemised lines (allowances/bonus/overtime/deduction/advance), approve/pay (method-agnostic), and self-service (`/payslips/me`, owner-readable `/payslips/{id}`).
## Local Contracts
- Admin/accountant manage; employees & teachers read only their own. Duplicate staff+period+period_type rejected (409). Built on existing `PayrollRecord` (extended with nullable breakdown columns) + `PayrollAdjustment`; the legacy `/operations` payroll CRUD is unaffected.
## Verification
- `python -m pytest backend/test_payroll.py`
