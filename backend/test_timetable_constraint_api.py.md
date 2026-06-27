# test_timetable_constraint_api.py

## Purpose

- Verifies the constraint-rule CRUD API: unsupported rule types are rejected, a created rule is listed, `/education/timetables/validate` reports the configured rule for a violating slot and clears once the rule is deleted.
- Verifies constraint rules are isolated by school (session-level: another school neither sees nor can delete a school's rule).

## Verification

- `python -m pytest backend/test_timetable_constraint_api.py`
