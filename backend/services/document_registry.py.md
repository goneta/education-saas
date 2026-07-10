# document_registry.py
## Source File
- `backend/services/document_registry.py`
## Purpose
- Universal authenticity layer for every generated document. `register(...)` mints
  a public UUID + content hash + type-specific JSON payload (idempotent per
  source_type/source_id). `qr_data`/`qr_text` produce the JSON encoded in the QR;
  `render_qr_png` (qrcode+Pillow) and `draw_qr_on_canvas` (reportlab drawImage)
  stamp it. `verify(uuid)` resolves the public authenticity record; `revoke`.
## Local Contracts
- Verification URL from `DOCUMENT_VERIFY_BASE_URL` env (default https://teducai.com)
  → `/verify/{uuid}`. Cross-cutting, zero duplication: a row references the source,
  storing only a verifiable snapshot. content_hash = sha256 of canonical payload.
## Verification
- `python -m pytest backend/test_document_registry.py`
