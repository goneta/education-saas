# page.tsx

## Source File

- `frontend/app/[locale]/emploi/etudiant/page.tsx`

## Purpose

- Public registration page for external students who need a TeducAI Emploi CV and sharecode without access to school dashboards.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- External student registration posts to the employment API and should not grant school-scoped dashboard data.
- Payment state is returned by the backend and should remain visible to the user.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/emploi/etudiant/page.tsx"`
