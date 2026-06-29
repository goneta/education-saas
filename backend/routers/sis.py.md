# sis.py

## Source File

- `backend/routers/sis.py`

## Purpose

- Student Information System extensions (`/sis`): multiple guardians, emergency contacts (priority-ordered), and one confidential medical record per student.

## Local Contracts

- Every endpoint resolves the student's school via the linked `User` and enforces tenant isolation (`_student_in_school`). Demographic writes are admin-gated; medical read/write is restricted to `MEDICAL_ROLES` (super-admin/school-admin/direction). Medical record is upsert (unique per student).

## Verification

- `python -m pytest backend/test_sis.py`
