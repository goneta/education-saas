# payroll.py (service)
## Source File
- `backend/services/payroll.py`
## Purpose
- Country-extensible payroll calculation engine. `compute()` turns base pay + lines into a gross→net breakdown (social contributions, taxable base, income tax, deductions, advances, net). Register country rules with `@register("SN")`; default is flat-rate. `base_amount_for()` resolves period base from rate × units.
## Verification
- `python -m pytest backend/test_payroll.py::test_engine_breakdown_is_correct`
