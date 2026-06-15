# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/account/[section]/page.tsx`

## Purpose

- Renders the account menu destination pages: overview, renewals, security, sessions, contact, payment methods, account credit, invoices, preferences, email notifications, team members, and referral.
- Uses authenticated account preferences, notifications, and payment history APIs.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep section keys in sync with dashboard sidebar account links.
- Preferences must save to `/account/preferences` and theme changes must remain instant through `ThemeProvider`.
- Payment-related sections should continue to show both platform and school payment history where authorized.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/account/[section]/page.tsx"`
