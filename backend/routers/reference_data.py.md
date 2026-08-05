# reference_data.py (router)
## Source File
- `backend/routers/reference_data.py`
## Purpose
- `/reference-data` API over services/reference_data.py: `GET /categories`
  (registry + fr/en labels), `GET /{category}` (the MERGED 🌐+🏫 list for the
  caller's school; super-admin may pass ?school_id=; ?include_inactive=true for
  management pages), `POST /{category}` (super-admin -> global by default;
  school admin/direction -> always local), `PATCH|DELETE /items/{id}` (permission
  rules enforced in the service; global rows 403 for schools).
## Verification
- `python -m pytest backend/test_reference_data.py`
