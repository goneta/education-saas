# verify.py
## Source File
- `backend/routers/verify.py`
## Purpose
- Public (UNAUTHENTICATED) `GET /verify/{uuid}` — the target of the QR code on every
  generated document. Returns a safe authenticity summary (valid/revoked/not_found,
  type, school, issued-to, date, status) via services/document_registry.verify.
## Verification
- `python -m pytest backend/test_document_registry.py -k verify`
