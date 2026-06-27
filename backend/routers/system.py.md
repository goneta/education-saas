# system.py

## Source File

- `backend/routers/system.py`

## Purpose

- Owns tenant-scoped school settings, secure logo upload/public delivery, persistent subscription changes, user administration, role/permission management, templates, and audit APIs.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Paid subscription changes create pending platform payments; only Free is activated immediately, and legacy Super Admin updates cannot bypass payment confirmation.
- Managed user deletion is soft, audited, tenant-scoped, and protects administrator boundaries.
- Role catalogs deduplicate global and school-specific definitions by stable role key and ignore soft-deleted users in membership counts and listings.
- Privilege escalation is blocked for non-super-admins: `_assign_user_roles` rejects the wildcard role keys `super_admin`/`school_admin`/`admin` (a user's own primary role is exempt), and user create/update reject setting those wildcard primary roles. Only the platform Super Admin may grant them.
- School logos support secure upload, public internal rendering, replacement, and audited deletion.
- User profile photos support authenticated tenant-scoped read, self/admin upload, and audited deletion.
- Legacy school-template application delegates to assignment-scoped idempotent seeding.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
