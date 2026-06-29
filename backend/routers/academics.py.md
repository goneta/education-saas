# academics.py

## Source File

- `backend/routers/academics.py`

## Purpose

- `/academics/students/{id}/gpa?term_id=`: automatic weighted GPA for a student (optionally a term), tenant-scoped via the student's institution.

## Verification

- `python -m pytest backend/test_academics.py`
