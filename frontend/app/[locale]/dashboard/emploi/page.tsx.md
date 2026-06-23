# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/emploi/page.tsx`

## Purpose

- Authenticated student TeducAI Emploi workspace for CV details, sharecode regeneration, privacy settings, job-seeking status, skills/languages/sectors, and work history.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- The page must rely on backend privacy and ownership enforcement; frontend toggles are not authorization controls.
- Keep controls compact, mobile-safe, and dark-mode readable inside the dashboard shell.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/emploi/page.tsx"`
