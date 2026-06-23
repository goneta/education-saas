# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/emploi-recruteur/page.tsx`

## Purpose

- Authenticated recruiter workspace for creating job offers, viewing own offers, closing/archiving offers, and listing received applications.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Recruiter actions must remain scoped by backend recruiter profile ownership.
- Deleting an offer with applications should archive it rather than physically removing it.
- Pending-payment recruiters can open and navigate the dashboard, see a red `Paiement: pending` banner, and receive a payment modal when attempting premium actions.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/emploi-recruteur/page.tsx"`
