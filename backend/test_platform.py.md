# test_platform.py

## Purpose

- Verifies Core Platform Slice 1: department CRUD + tenant isolation + admin-only writes; feature-flag override falling back to the platform default (and upsert without duplicates); global search typed + tenant-scoped + short-query guard.

## Verification

- `python -m pytest backend/test_platform.py`
