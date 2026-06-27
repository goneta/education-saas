# test_portal_isolation.py

## Purpose

- Verifies the `/documents/portal` parent/student isolation: a parent with no active `ParentStudentLink` sees no documents (not the whole school).
- Verifies a linked parent sees only their own child's documents.
- Verifies an unlinked parent cannot target another student via the `student_id` query parameter (403).

## Verification

- `python -m pytest backend/test_portal_isolation.py`
