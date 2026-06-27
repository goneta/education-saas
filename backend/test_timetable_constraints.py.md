# test_timetable_constraints.py

## Purpose

- Unit-tests the configurable constraint engine handlers: subject time window, teacher available days, subject no-consecutive-days, subject-after-forbidden (precedence), and that inactive rules are ignored.

## Verification

- `python -m pytest backend/test_timetable_constraints.py`
