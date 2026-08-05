# test_reference_data.py
## Source File
- `backend/test_reference_data.py`
## Purpose
- Global+local merge and cross-school isolation (school B never sees school A's
  local items); schools cannot create/update/delete global items (403) while the
  Super Admin can; local lifecycle (create/update/delete by the owning school
  only, 403 for another school, 409 duplicate code in the merged view);
  `school_level` merges the existing SchoolLevel referential (source "levels")
  with local reference additions; unknown category -> 404. In-memory SQLite.
## Verification
- `python -m pytest backend/test_reference_data.py` (5 green).
