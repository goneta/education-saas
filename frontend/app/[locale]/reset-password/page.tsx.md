# reset-password/page.tsx
## Source File
- `frontend/app/[locale]/reset-password/page.tsx`
- SEC-05: target of the e-mailed link (`?token=`). Confirms the password twice,
  states the policy, handles a missing/invalid/expired token explicitly, and
  tells the user that all previously open sessions were revoked. Redirects to
  the login page on success.
