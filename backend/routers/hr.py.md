# hr.py

## Source File
- `backend/routers/hr.py`

## Purpose
- Human Resources (`/hr`): staff leave self-service + approval workflow, built on the EXISTING `models.LeaveRequest` (not a new table). Adds self-service create (staff_user_id from caller), own/all list scoping, and the approve/reject decision with requester notification.

## Local Contracts
- Tenant-scoped. Non-approver staff see only their own requests; only APPROVER_ROLES can decide. The admin `/enterprise/leaves` endpoints still exist for full-list management — this router does not duplicate the model.

## Verification
- `python -m pytest backend/test_hr.py`
