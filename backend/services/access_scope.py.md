# access_scope.py
## Source File
- `backend/services/access_scope.py`
## Purpose
- Single source of truth for INTRA-tenant row-level authorization (audit
  PRIV-01/PRIV-02): which students a user may see inside their own school.
  `visible_student_ids(db, user)` returns `None` for staff (no row restriction),
  `{own_id}` for a learner, the linked children for a parent, and an EMPTY set
  for anyone else — an empty set must yield an empty result, never all rows.
  `can_view_student(db, user, student_id)` is the per-record form;
  `is_staff`, `own_student_id`, `linked_child_ids` are the building blocks.
## Local Contracts
- School scoping remains the caller's job; this module answers ONLY the
  row-level question. Any endpoint returning data about a named student must go
  through it instead of settling for "same school".
- `STAFF_ROLES` lists the roles that legitimately work on the whole student body
  (administration, direction, pedagogy, teachers, front office, finance).
- Consumers: `routers/school_life.py` (Discipline/Internat row filtering, list +
  detail + CSV export), `routers/academics.py` (GPA, unauthorized access masked
  as 404).
## Verification
- `python -m pytest backend/test_access_scope.py` (5 green).
