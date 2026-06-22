# header.tsx

## Source File

- `frontend/components/dashboard/header.tsx`

## Purpose

- Owns dashboard search, active organization/school/model/year selector, notification center, persistent theme toggle, cart popover, checkout navigation, and locale switching.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Notification and cart controls use authenticated `/account` APIs.
- Shared labels must use the translation catalogs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
