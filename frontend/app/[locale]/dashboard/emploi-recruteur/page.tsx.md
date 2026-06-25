# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/emploi-recruteur/page.tsx`

## Purpose

- Authenticated recruiter ATS workspace for company profile/logo metadata, subscriptions, AI credits, enriched job offers, automatic candidate matching, ShareCode lookup, recruiter AI agent, own offers, archiving, and received applications.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Recruiter actions must remain scoped by backend recruiter profile ownership.
- Deleting an offer with applications should archive it rather than physically removing it.
- Pending-payment recruiters can open and navigate the dashboard, see a red `Paiement: pending` banner, and receive a payment modal when attempting premium actions.
- The page must not auto-call premium application/CV endpoints for pending recruiters; restricted reads are triggered by explicit actions and show the payment modal.
- Logo/photo previews accept recruiter-managed URLs or compact data URLs; backend ownership and storage policy remain authoritative for any future binary upload endpoint.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/emploi-recruteur/page.tsx"`
