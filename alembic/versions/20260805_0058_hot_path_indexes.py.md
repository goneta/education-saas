# 20260805_0058_hot_path_indexes.py
## Source File
- `alembic/versions/20260805_0058_hot_path_indexes.py`
## Purpose
- Audit PERF-01: creates the 98 missing single-column indexes on the hot
  tenant/scope foreign keys (`school_id` x51, `student_id` x19, `class_id` x9,
  `academic_year_id` x7, `subject_id` x5, `teacher_id` x4, `user_id` x3).
  Every query of this multi-tenant platform filters by school_id, so without
  them the cost grew with the volume of the WHOLE platform instead of the
  institution's.
## Local Contracts
- The (table, column) list was computed from the models at authoring time and
  FROZEN in the file, so a later model change can never retroactively alter this
  migration. Idempotent: an index is created only when the table/column exists
  and no single-column index already covers it. Index-only, no data change.
## Verification
- `python -m alembic upgrade head` (applied: 98 index creations).
