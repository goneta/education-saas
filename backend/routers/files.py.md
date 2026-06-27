# files.py

## Source File

- `backend/routers/files.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Owns secure file upload, listing, download, signed URLs, sharing, approval, and deletion. Access is gated by `_query_file`/`_can_access_file` (owner, same-school admin, super admin, approved public, or active share) so cross-tenant access returns 404; lists are scoped the same way.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Upload metadata from `file_storage.store_upload` already contains the display name and must not be supplied a second time.
- Share revocation is limited to the share creator, the platform Super Admin, or an admin of the file's own school; a school admin cannot revoke another school's shares.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
