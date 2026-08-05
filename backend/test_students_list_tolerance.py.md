# test_students_list_tolerance.py
## Source File
- `backend/test_students_list_tolerance.py`
## Purpose
- Root-cause coverage for the "liste des élèves vide" bug: students pinned to a
  stale (inactive/replaced) school-model assignment, pinned to the active one and
  unpinned must ALL appear in `GET /students` for their school's active context;
  other schools' students never leak in. Also checks `/students/diagnostics`
  (stage counts + hints, empty vs one-student cases).
- Self-contained in-memory SQLite (Organization → School → SchoolModel/SMA old
  inactive + new active → users) calling the router functions directly — does NOT
  depend on the dev database, unlike `test_students.py`.
## Verification
- `python -m pytest backend/test_students_list_tolerance.py` (2 green).
