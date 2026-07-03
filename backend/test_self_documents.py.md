# test_self_documents.py — Tests for self-service documents (automation B)

## Coverage

- Student generates certificate + attestation; rows land in the existing
  `GeneratedDocument` table with `source_type="self_service"` and the right
  `GeneratedDocumentType` mapping (CERTIFICATE / OTHER / RECEIPT).
- Parent generates for a linked child only (`ParentStudentLink`); an unlinked
  child → 403; `parent_user_id` is recorded on the document.
- Receipt: `my-payments` lists only the student's own successful payments;
  generating a receipt for another student's payment → 404; `source_id` points
  at the payment and `outstanding_after` is computed.
- `/mine` returns the stored payloads; `/verify/{reference}` validates a real
  reference and rejects an unknown one.
- `/children`: student sees self, parent sees linked children only.
- RBAC: teacher → 403; admin without `student_id` → 400; admin with a student
  of another school → 404 (tenant isolation).

## Pattern

In-memory SQLite (StaticPool) + direct router-function calls — same fixture
style as `test_fee_reminders.py`.
