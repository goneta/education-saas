# forgot-password/page.tsx
## Source File
- `frontend/app/[locale]/forgot-password/page.tsx`
## Purpose
- SEC-05: public page requesting a reset link. Always shows the same
  confirmation whether or not the address has an account (no enumeration), and
  surfaces the server's 503 honestly when SMTP is not configured instead of
  pretending a mail was sent. Linked from the login form.
