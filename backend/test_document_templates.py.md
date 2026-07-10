# test_document_templates.py
## Source File
- `backend/test_document_templates.py`
## Purpose
- CRUD + auto/set-default exclusivity + duplicate + RBAC/cross-school; field engine
  (real student/class/year data, overrides, unknown-key substitution); generation
  (registry row with spec payload, verifiable via /verify, real %PDF, default-template
  resolution, 404/422 guards); preview (watermark, registry untouched); placeholders.
## Verification
- `python -m pytest backend/test_document_templates.py` (5 green).
