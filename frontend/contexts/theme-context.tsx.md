# theme-context.tsx

## Source File

- `frontend/contexts/theme-context.tsx`

## Purpose

- Provides TeducAI light/dark/system theme state to the frontend.
- Applies the effective theme to `document.documentElement`, stores local preference, and synchronizes authenticated preference with `/account/preferences`.
- Tracks live operating-system theme changes while system mode is selected.

## DOX Scope

- Nearest contract: `frontend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep theme changes instant and global.
- Preserve local storage fallback for logged-out/public pages.
- Do not make theme application dependent on a dashboard-only component.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint contexts/theme-context.tsx"`
- Full build when changing provider behavior.
