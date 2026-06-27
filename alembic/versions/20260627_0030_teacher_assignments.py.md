# 20260627_0030_teacher_assignments.py

## Purpose

- Creates the `teacher_assignments` table enabling a teacher to teach concurrently at several schools/models, and backfills one primary assignment per existing teacher.

## Local Contracts

- Unique on `(user_id, school_model_assignment_id)` so a teacher has at most one assignment per model context.
- Backfill derives each existing teacher's primary assignment from `teacher_profiles` joined to `users.school_id`; bound boolean params keep it dialect-safe (Postgres prod, SQLite tests). No existing data is lost.

## Verification

- `python -m alembic heads`
- `python -m py_compile backend\models.py`
