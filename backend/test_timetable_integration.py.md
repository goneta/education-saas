# test_timetable_integration.py

## Purpose

- Verifies `/timetables/teacher-load` aggregates per-teacher weekly sessions/minutes/hours from the timetable (HR/payroll integration).
- Verifies applying a substitution reassigns the course teacher and emits a `timetable.substituted` notification to the substitute.

## Verification

- `python -m pytest backend/test_timetable_integration.py`
