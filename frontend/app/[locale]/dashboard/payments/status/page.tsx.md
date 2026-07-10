# page.tsx (Payment status)
## Source File
- `frontend/app/[locale]/dashboard/payments/status/page.tsx`
## Purpose
- Post-checkout landing page (CinetPay return_url appends ?transaction_id=…; internal links
  use ?ref=…). Calls POST /payments/{ref}/refresh — server-side gateway verification — and
  renders checking / pending (auto-poll 7s) / success / failure / unknown states with retry
  and receipts links. i18n namespace `payStatus` (FR/EN full, es/sw = EN).
## Verification
- FE build unavailable in sandbox — verified by inspection.
