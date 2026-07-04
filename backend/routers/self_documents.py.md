# self_documents.py — Self-service administrative documents (automation B)

## Purpose

Lets students (and parents, for their linked children) generate official
administrative documents on request without any staff involvement: certificat
de scolarité, attestation de fréquentation, and payment receipts. Frees the
school office from repetitive document requests.

## Design

- **No new table.** Documents are recorded in the existing `GeneratedDocument`
  model (`source_type="self_service"`) — document_type CERTIFICATE (certificat),
  OTHER (attestation), RECEIPT (reçu); the full render payload is stored in
  `content` so a document can be re-displayed identically forever.
- **Unique reference** per document (`CERT-…`, `ATT-…`, `REC-…` + 10 hex chars)
  printed on the document; `GET /self-documents/verify/{reference}` performs the
  authenticity check.
- **Access model** (`_resolve_student`): a STUDENT/PUPIL resolves to their own
  profile; a PARENT must pass `student_id` and hold a `ParentStudentLink`; staff
  (SUPER_ADMIN/SCHOOL_ADMIN/DIRECTION/SECRETARY/REGISTRAR) may pass any student
  of their school (Super Admin: any). Everyone else → 403.
- **Rendering** is print-friendly HTML on the frontend (`my-documents` page)
  built from the stored payload — PDF export stays on the NOT-READY list.
- Every generation is audited (`self_document.<type>.generated`).

## Endpoints (prefix `/self-documents`)

- `GET /children` — students the caller may generate for (self, or linked children).
- `POST /certificate` / `POST /attestation` — generate + persist, returns the payload.
- `GET /my-payments` — the student's successful payments (receipt candidates).
- `POST /receipt/{payment_id}` — receipt for one of the student's own payments
  (404 if the payment belongs to another student); includes outstanding-after.
- `GET /mine` — the student's self-service documents (payload included for reprint).
- `GET /verify/{reference}` — authenticity check (any authenticated user).

## Verification

- `python -m pytest backend/test_self_documents.py`
- Import smoke check: `python -c "import backend.main"`.
- E-signature: `POST /self-documents/{id}/sign` (document's student or linked parent only, 409 on double-sign); `/mine` and `/verify/{reference}` now include the signatures with live authenticity + tamper checks.
