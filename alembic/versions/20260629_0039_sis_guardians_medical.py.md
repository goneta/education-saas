# 20260629_0039_sis_guardians_medical.py

## Purpose

- Creates `student_guardians`, `student_emergency_contacts`, and `student_medical_records` (one per student, unique).

## Local Contracts

- All FK to `student_profiles`; tenant scope resolved via the student's user. Additive; legacy `parent_*` fields on StudentProfile remain.

## Verification

- `python -m alembic upgrade head`; `python -m pytest backend/test_sis.py`
