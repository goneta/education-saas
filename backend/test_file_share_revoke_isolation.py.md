# test_file_share_revoke_isolation.py

## Purpose

- Verifies an admin of another school cannot revoke a document share whose file belongs to a different school (403, share left active).
- Verifies the owning school's admin (here the creator) can revoke the share.

## Verification

- `python -m pytest backend/test_file_share_revoke_isolation.py`
