# teacher_assignments.py

## Source File

- `backend/services/teacher_assignments.py`

## Purpose

- Helpers for multi-school teaching: resolve whether a teacher is accessible to a caller (super admin, or an active `TeacherAssignment` in the caller's school) and idempotently attach a teacher to a school/model context.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- `TeacherProfile` stays the single global identity (unique per user); `TeacherAssignment` carries the per-school/model engagements, mirroring `StudentEnrollment` for learners.
- `ensure_assignment` is idempotent on `(user_id, school_model_assignment_id)`, reactivates an ended assignment instead of duplicating, and flags the teacher's first assignment as primary.

## Verification

- python -m py_compile backend\services\teacher_assignments.py; python -m pytest backend/test_teacher_multi_school.py
