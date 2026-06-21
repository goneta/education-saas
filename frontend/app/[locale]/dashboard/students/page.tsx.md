# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/students/page.tsx`

## Purpose

- Loads and displays the tenant-scoped student list and coordinates student create, edit, delete, search, and detail navigation.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Uses the canonical `/students` collection endpoint without redirect.
- API failures must be shown to the user instead of being presented as an empty list.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
