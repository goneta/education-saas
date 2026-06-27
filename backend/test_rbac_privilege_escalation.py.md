# test_rbac_privilege_escalation.py

## Purpose

- Verifies a non-super-admin (school admin) cannot grant the wildcard role keys `super_admin`/`school_admin`/`admin` via `PUT /system/users/{id}/roles` (403), while a normal role key still works.
- Verifies a school admin cannot create a user with a wildcard admin primary role, nor promote an existing user to one (403).

## Verification

- `python -m pytest backend/test_rbac_privilege_escalation.py`
