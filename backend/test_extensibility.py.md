# test_extensibility.py
## Purpose
- Slice 7: emit_event subscription matching (specific + catch-all, not other events), tenant scoping, API key returned-once + hashed + revoke, retry max-attempts 409 and non-admin 403.
## Verification
- `python -m pytest backend/test_extensibility.py`
