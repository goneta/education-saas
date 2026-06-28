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
- Normalizes direct-array and wrapped collection responses, bypasses stale browser caches, and keeps the primary student list visible instead of allowing global auto-collapse.
- Student rows expose authenticated profile-photo display/upload and refresh the persisted list after replacement.

- Search uses the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it on collection pages instead of bespoke search inputs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
# Lifecycle navigation

The student list links to the global journey administration workspace for transfers, imports, and academic-year closure.
