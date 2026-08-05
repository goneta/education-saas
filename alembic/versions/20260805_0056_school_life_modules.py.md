# 20260805_0056_school_life_modules.py
## Source File
- `alembic/versions/20260805_0056_school_life_modules.py`
## Purpose
- Creates discipline_records, school_activities, health_records,
  boarding_records (school/student-scoped, status server-defaults, indexes) and
  EXTENDS the existing exam_sessions column-only (subject_id as plain Integer —
  SQLite cannot ALTER-add a constrained column — duration_minutes, room,
  max_score, coefficient, notes). Seeds the three new GLOBAL reference
  categories: activity_type, incident_type, health_record_type (French labels).
  Idempotent (table/column/seed presence checks).
## Verification
- `python -m alembic upgrade head`
