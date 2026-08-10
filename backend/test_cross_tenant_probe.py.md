# test_cross_tenant_probe.py
## Source File
- `backend/test_cross_tenant_probe.py`
## Purpose
- Regression net for cross-tenant (IDOR) leaks: School A's admin attacks School
  B's identifiers across 7 surfaces (student, teacher, report card JSON + PDF,
  class roster, attendance, receipt PDF). Each must answer 403/404.
## Local Contracts
- `access_scope` cannot cover this class of bug: it answers the row-level
  question and returns "no restriction" for staff. Only an explicit tenancy
  filter stops identifier walking.
- **Negative tests alone are not enough**: this suite passes when an endpoint is
  broken for everyone (404 for all). Pair it with a positive test
  (`test_deep_grades.py`) — that pairing is what caught P3-A.
## Verification
- `python -m pytest backend/test_cross_tenant_probe.py` (7 green).
