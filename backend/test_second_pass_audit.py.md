# test_second_pass_audit.py
## Source File
- `backend/test_second_pass_audit.py`
## Purpose
- Second verification pass (6 aout 2026). Non-regression tests for the defects
  found when re-reading the remediation code itself:
  BUG-B `registry_source_id` is injective (student 1/term 23 vs 12/term 3 used to
  collide) and two students get two distinct registry entries;
  BUG-D the attendance list is paginated (default 200, hard cap 500) and row
  scoped (a learner sees only their own records, a parent only their children's,
  even when passing another student_id);
  plus the "no visible student" path (empty allow-set must yield an empty list,
  never the whole school) exercised end to end on attendance AND school-life.
## Verification
- `python -m pytest backend/test_second_pass_audit.py` (5 green).
