# test_personnel.py
## Purpose
- #7: staff creation auto-creates an active user (role/school) + generated password; duplicate email 409 / unknown role 422; status update + deactivate-on-delete; non-admin 403.
## Verification
- `python -m pytest backend/test_personnel.py`
- Also covers #3 assignment history: initial membership on creation, cross-establishment add (Super Admin only / 403 for school-admin), end-keeps-history, duplicate active 409.
