# document_templates.py
## Source File
- `backend/routers/document_templates.py`
## Purpose
- `/document-templates`: list/create/patch/delete, duplicate, set-default,
  background upload (PDF/DOCX/PNG/JPG via file_storage, 422 otherwise),
  `GET /placeholders`, `POST /{id}/preview` (watermarked sample PDF),
  `POST /generate` (real student → registry + QR-stamped PDF download).
## Local Contracts
- RBAC: SUPER_ADMIN/SCHOOL_ADMIN/DIRECTOR; school-scoped (404 cross-school);
  Super-Admin passes school_id. Generate resolves template_id → its kind, else the
  school default for `kind`; 422 without either; 404 unknown student in school.
## Verification
- `python -m pytest backend/test_document_templates.py`
