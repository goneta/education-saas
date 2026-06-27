# test_timetable_optimizer.py

## Purpose

- Verifies the optimiser returns the requested number of candidates, scored (0–100) and sorted best-first with a breakdown.
- Verifies candidates contain no hard conflicts (no class or teacher double-booking).
- Verifies a `teacher_available_days` rule is respected (no placement for that teacher outside the allowed days).

## Verification

- `python -m pytest backend/test_timetable_optimizer.py`
