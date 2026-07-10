# document_templates.py
## Source File
- `backend/services/document_templates.py`
## Purpose
- Diploma & certificate template engine. CRUD/duplicate/set-default (one default per
  school+kind; first created auto-defaults), a `{{placeholder}}` field engine resolved
  from REAL data (student name/matricule, current class, current AcademicYear,
  auto DIP-/CERT- numbers; overrides win; unknown override keys substitutable →
  extensible), and a reportlab A4-landscape renderer.
## Local Contracts
- Backgrounds: PNG/JPG drawn full-page; PDF merged under the foreground via pypdf;
  DOCX stored but rendered with the standard layout (never faked). QR top-right via
  document_registry.draw_qr_on_canvas; QR/background failures never break rendering.
- `generate(...)` registers in DocumentRegistry (document_type=diploma|certificate,
  spec payload) then renders the QR-stamped PDF; audited
  (document_template.* / document_template.generated.*). Preview = sample fields +
  PREVIEW watermark, no QR, never registered.
## Verification
- `python -m pytest backend/test_document_templates.py`
