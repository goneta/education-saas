# test_document_registry.py
## Source File
- `backend/test_document_registry.py`
## Purpose
- Registry idempotency + hashing, qr_data/PNG, verify (valid/not_found/revoked), and
  the invoice integration (attach_registry injects uuid/verify_url/qr_text, PDF is a
  real %PDF, registry row is verifiable and not duplicated on re-generation).
## Verification
- `python -m pytest backend/test_document_registry.py` (4 tests green).
