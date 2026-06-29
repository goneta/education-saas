# test_sis.py

## Purpose

- Verifies SIS Slice 2: guardians + emergency contacts (primary-first ordering), medical record upsert (single row) with role restriction (teacher denied), cross-school student rejection (404), and admin-only writes.

## Verification

- `python -m pytest backend/test_sis.py`
