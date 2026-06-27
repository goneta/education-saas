# test_admission_roster_visibility.py

## Purpose

- Verifies a student enrolled through `/operations/admissions/{id}/enroll` appears in the standard `/students` roster, i.e. the admission path creates a `StudentGlobalProfile` + `StudentEnrollment` (the roster only lists students that have an enrollment).

## Verification

- `python -m pytest backend/test_admission_roster_visibility.py`
