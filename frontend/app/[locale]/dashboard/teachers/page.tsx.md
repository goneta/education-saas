# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/teachers/page.tsx`

## Purpose

- Loads and displays the tenant-scoped teacher list and coordinates teacher create, edit, delete, and search actions.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Uses the canonical `/teachers` collection endpoint without redirect.
- API failures must be passed to the list component instead of silently rendering an empty result.
- Normalizes direct-array and wrapped collection responses and bypasses stale browser caches before passing data to the table.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
