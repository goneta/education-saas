# test_timetable_substitution.py

## Purpose

- Verifies substitute proposals include only teachers free at the slot (busy/self excluded), respect the `teacher_available_days` rule, and return nothing when the teacher has no courses that day.

## Verification

- `python -m pytest backend/test_timetable_substitution.py`
