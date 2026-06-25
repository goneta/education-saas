# page.tsx

## Source File

- `frontend/app/[locale]/help/page.tsx`

## Purpose

- Standalone localized help route used by dashboard help modals and drawers so only help content renders, without the dashboard sidebar, top bar, or AI agent panel.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Reuse `HelpContent` from the dashboard help page so page, modal, and drawer modes stay in sync.
- Keep the route light/dark mode readable and free from dashboard layout dependencies.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/help/page.tsx"`
