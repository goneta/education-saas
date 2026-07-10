# page.tsx (public /verify/{uuid})
## Source File
- `frontend/app/[locale]/verify/[uuid]/page.tsx`
## Purpose
- Public document-verification page reached by scanning a document QR. Client
  component; fetches the public `/verify/{uuid}` API and shows authentic / revoked /
  not-found with the main info (type, reference, school, issued-to, date, status).
## Local Contracts
- No auth. Inline FR/EN strings (es/sw -> EN) so it needs no next-intl messages.
## Verification
- FE build unavailable in sandbox — verified by inspection (brace/backtick balance).
