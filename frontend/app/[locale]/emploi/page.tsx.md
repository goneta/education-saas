# page.tsx

## Source File

- `frontend/app/[locale]/emploi/page.tsx`

## Purpose

- Public TeducAI Emploi page with sharecode lookup, sector-based public CV search, published job offers, and links to external student and recruiter registration.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Public CV rendering must only display fields returned by the backend public payload.
- Keep sharecode errors generic and avoid exposing partial student existence.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/emploi/page.tsx"`
