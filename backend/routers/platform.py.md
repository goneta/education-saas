# platform.py

## Source File

- `backend/routers/platform.py`

## Purpose

- Core Platform admin API (`/platform`): departments CRUD, feature flags (per-institution override over a platform default, with a reusable `feature_enabled` helper), and a tenant-scoped global search across students/teachers/classes/fees.

## Local Contracts

- Tenant-scoped via `_school_id`; writes gated to admin roles. `feature_enabled(db, key, school_id)` resolves a school override first, then the `school_id IS NULL` platform default — any module can call it to gate a capability. Global search enforces `school_id` on every query and ignores queries shorter than 2 chars.

## Verification

- `python -m pytest backend/test_platform.py`
