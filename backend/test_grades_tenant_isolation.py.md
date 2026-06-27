# test_grades_tenant_isolation.py

## Purpose

- Verifies assessments are isolated by school: a second school cannot read, list grades of, update, or delete another school's assessment (404), and cannot create an assessment against another school's class (404).
- Verifies the owner still reads its own assessment after the rejected cross-tenant attempts.

## Verification

- `python -m pytest backend/test_grades_tenant_isolation.py`
