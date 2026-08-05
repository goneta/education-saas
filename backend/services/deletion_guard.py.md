# deletion_guard.py
## Source File
- `backend/services/deletion_guard.py`
## Purpose
- Explicit deletion policy for referenced master data (audit DATA-01). The schema
  declares NO `ON DELETE` rule while routers physically delete rows, so removing
  a referenced record either raised an opaque 500 (PostgreSQL FK violation) or
  silently destroyed dependents through an ORM cascade. `ensure_deletable`
  raises a **409** naming every blocker and its count, in French;
  `blocking_references` returns the raw (label, count) pairs.
- Declared maps: `CLASS_REFERENCES` (students, enrolments, timetable slots,
  assignments, assessments, exam sessions, activities, fees),
  `SUBJECT_REFERENCES` (timetable, assignments, assessments, exams),
  `ASSESSMENT_REFERENCES` (grades).
## Local Contracts
- Any new physical delete of master data MUST declare its references here rather
  than relying on the database to fail. Adding a dependency = one `Reference`
  line. Entities carrying history should prefer a logical delete instead.
- Consumers: `routers/education.py` (class, subject), `routers/grades.py`
  (assessment).
## Verification
- `python -m pytest backend/test_deletion_guard.py` (4 green).
