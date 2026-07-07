# page.tsx (Finance → Billing)
## Source File
- `frontend/app/[locale]/dashboard/finance/billing/page.tsx`
## Purpose
- Enterprise Billing & Subscription page. Single tabbed client page (Overview,
  Subscription, Payment methods, Billing history, Credits, Usage, Transactions,
  Promotions, Preferences, Tax & VAT, Audit logs) wired to `/billing/*`. Super-Admin
  sees revenue KPIs on Overview. Light/dark, responsive.
## Local Contracts
- i18n namespace `billing` (FR/EN full; es/sw fall back to EN text). Dynamic `t()` keys
  are cast to literals (next-intl strict typing). Subscription switching posts to the
  existing `/system/subscription/change`; credits/payment-methods deep-link to the
  existing `/dashboard/ai-credits` and `/dashboard/account/payment-methods` pages.
- Roadmap (documented, NOT built here): invoice PDF/print/email, live usage charts,
  saved payment-method cards UI, AI billing assistant. Underlying data already exists.
## Verification
- Frontend build unavailable in sandbox — verified by inspection (brace/paren balance,
  all icons imported, all dynamic `t()` keys cast, i18n key parity across 4 locales).
- Invoice PDF: the Billing-history "Download PDF" button now fetches `/billing/invoices/{id}/pdf` as a blob (bearer auth) and triggers a real .pdf download (reportlab-generated server-side). No longer a placeholder.
