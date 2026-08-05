# test_deletion_guard.py
## Source File
- `backend/test_deletion_guard.py`
## Purpose
- Lot 3 of the audit remediation (DATA-01): an unreferenced class/subject stays
  deletable; a timetable slot blocks BOTH its class and its subject (the latter
  had no guard at all) with an actionable 409 naming the blocker and its count;
  every declared class dependency is detected (students, assignments,
  activities); an assessment holding grades cannot be deleted.
## Verification
- `python -m pytest backend/test_deletion_guard.py` (4 green).
