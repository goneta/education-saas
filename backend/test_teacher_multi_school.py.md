# test_teacher_multi_school.py

## Purpose

- Verifies a teacher can teach at two schools concurrently: assigning them to a second school is additive (both schools list them), not a transfer.
- Verifies removing a teacher from one school keeps their engagement at the other.
- Verifies a school without an active assignment for a teacher cannot view that teacher's detail (404).

## Verification

- `python -m pytest backend/test_teacher_multi_school.py`
