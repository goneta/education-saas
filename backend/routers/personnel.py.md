# personnel.py
## Source File
- `backend/routers/personnel.py`
## Purpose
- Personnel scolaire (#7): CRUD for school staff. Creating a staff member auto-creates the underlying User (with the chosen primary role + school) and a `StaffProfile` (department, function, additional roles, status). School-scoped; School-Admin/Super-Admin only.
## Local Contracts
- Primary + additional roles validated against `UserRole`. Email uniqueness enforced (409). Status in {active,inactive,suspended,on_leave}. DELETE removes the profile and deactivates the user (never hard-deletes). A generated temporary password is returned once at creation when none supplied.
## Verification
- `python -m pytest backend/test_personnel.py`
- #3 historisation: staff creation now records a `SchoolMembership` (establishment posting). New endpoints `GET/POST /personnel/{id}/assignments` + `POST /personnel/assignments/{id}/end` expose a staff member's multi-establishment posting history (reuses `SchoolMembership`; school-admins post only within their school, Super Admin anywhere).
- Security: create_staff validates caller-supplied passwords (validate_password_strength) and the auto-generated credential is policy-compliant.
