# my-documents/page.tsx — Self-service documents page (automation B)

## Purpose

Student/parent-facing page ("Mes documents") to generate administrative
documents without staff: certificat de scolarité, attestation de fréquentation
and payment receipts. Backed by `/self-documents/*`.

## Behaviour

- Loads `/self-documents/children`; parents with several linked children get a
  selector (students resolve to themselves automatically).
- Two generate cards (certificate / attestation) + a confirmed-payments table
  with a per-row "Reçu" button + a generated-documents history with reprint.
- `printDocument()` opens a print-ready window: school header (logo, address),
  formal body text (from the `selfDocs` i18n namespace, `{year}` interpolated),
  student/enrollment facts table, payment block for receipts, issue date,
  unique reference + verification hint, signature/stamp area; `window.print()`
  fires on load. Reprints rebuild the exact same document from the stored
  payload returned by `/self-documents/mine`.
- All copy via `useTranslations("selfDocs")` (FR/EN/ES/SW parity).

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/my-documents/page.tsx"`
- Backend contract: `python -m pytest backend/test_self_documents.py`.
