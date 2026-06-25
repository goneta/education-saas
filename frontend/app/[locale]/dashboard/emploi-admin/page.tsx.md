# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/emploi-admin/page.tsx`

## Purpose

- Super Admin TeducAI Emploi dashboard for platform-level statistics, recruiter status, CV inventory, job activity, and employment notifications.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- The page is visible only to `super_admin` users in the dashboard UI and must rely on backend Super Admin enforcement for data access.
- Mutating controls should use the `/employment/admin/*` APIs and must not bypass recruiter or student ownership checks in regular employment endpoints.
- Keep cards, forms, and lists dark-mode readable and mobile-safe.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/emploi-admin/page.tsx"`
