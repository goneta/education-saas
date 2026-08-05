# test_school_life.py
## Source File
- `backend/test_school_life.py`
## Purpose
- The shared CRUD contract once (in-memory app mounting the real router with
  dependency overrides): create/serialize with student_name, search by title
  AND student name, exact totals + pagination, patch, CSV export, cross-school
  isolation (404 on foreign rows, empty list), delete. Role gating (teacher
  reads activities but 403 on create; 422 naming the missing required field;
  404 for a student outside the school). Health: reads AND export 403 for
  non-admin roles.
## Verification
- `python -m pytest backend/test_school_life.py` (3 green).
