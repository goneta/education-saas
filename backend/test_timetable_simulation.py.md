# test_timetable_simulation.py

## Purpose

- Verifies `explain_candidate` produces human-readable statements (score, fill).
- Verifies `simulate` teacher-absent reports impact and never improves coverage (fewer teachers), extra-working-day never worsens coverage, and unknown scenarios return an error.

## Verification

- `python -m pytest backend/test_timetable_simulation.py`
