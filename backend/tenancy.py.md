# tenancy.py

## Source File

- `backend/tenancy.py`

## Purpose

- Centralizes multi-school tenant rules for users, school-scoped records, and transfer history.
- Provides helpers for super-admin global access, school-admin scoped access, school selection during creation, duplicate-person detection, and `school_memberships` transfer records.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Use these helpers instead of ad hoc `current_user.school_id` checks when a route can be used by `SUPER_ADMIN`.
- `SUPER_ADMIN` must remain global with `school_id = None`; school-dependent creation must require an explicit payload school.
- `SCHOOL_ADMIN` must remain scoped to `current_user.school_id`.
- Duplicate-person lookup prioritizes strong identifiers such as email, phone, reference, or registration number; name and birth date are used only when no strong identifier is supplied.

## Verification

- `python -m py_compile backend\tenancy.py`
- Run targeted multi-tenant tests when changing behavior.
