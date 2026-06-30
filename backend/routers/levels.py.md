# levels.py
## Source File
- `backend/routers/levels.py`
## Purpose
- School levels referential (`/levels`): global, platform-managed list (CP1…BTS). Reads open to any authenticated user (schools need it to create classes); writes are Super-Admin only. Delete blocked when a class references the level code (409).
## Local Contracts
- `Class.level` references `SchoolLevel.code` (string). Not tenant-scoped (global referential). Super-admin gate on create/update/delete; toggle via PATCH is_active.
## Verification
- `python -m pytest backend/test_levels.py`
