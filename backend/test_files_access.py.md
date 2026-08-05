# test_files_access.py
## Source File
- `backend/test_files_access.py`
## Purpose
- Lot 5 / audit QUAL-01: `routers/files.py` decides who may read every uploaded
  document (student files, payslips, medical scans) and had NO test. Covers:
  uploader and school admin read a private file; **another school never can**
  (cross-tenant, admin included); same-school colleagues need an explicit
  DocumentShare or approved `public_internal` visibility (a pending approval
  stays closed); the Super Admin reads any school's file.
## Verification
- `python -m pytest backend/test_files_access.py` (4 green).
