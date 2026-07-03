# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/emploi/page.tsx`

## Purpose

- Authenticated student TeducAI Emploi workspace for CV details, SecureFile-backed photo upload/preview/removal, sharecode regeneration, privacy settings, job-seeking status, detailed skills, languages, sectors, academic credentials, certificates, portfolio, work history, recommended jobs, checkout-based AI credit purchase, and the student employment AI agent.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- The page must rely on backend privacy and ownership enforcement; frontend toggles are not authorization controls.
- Keep controls compact, mobile-safe, and dark-mode readable inside the dashboard shell.
- Recommended jobs are informational until the authenticated student applies; application authorization and duplicate checks stay backend-owned.
- Detailed skills, academic credentials, and certificates open their full editable form immediately from `Ajouter`, support row-level save/delete, and persist through the CV update endpoint.
- Detailed skills, academic credentials, certificates, work history, and recommended jobs render as controlled accordions with smooth open/close behavior; each section keeps independent locally persisted open/closed state.
- Student AI credit purchase must route through `/dashboard/checkout?purchase=ai-credits` so credits are applied only by the payment flow.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/emploi/page.tsx"`
- Automation D (job-seekers): the "Offres recommandees" panel gains "Actualiser mon CV" (POST /me/cv/refresh) and per-offer "Analyse d'ecart" + "Lettre IA" buttons (result shown in a <pre> under the offer; one in-flight AI call at a time).
