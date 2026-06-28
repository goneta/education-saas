# main-layout.tsx

## Source File

- `frontend/components/layout/main-layout.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It provides reusable UI behavior.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Dashboard shell panels, top bar, sidebars, and main content use consistent shared dark surfaces.
- Mobile dashboard bottom navigation must use the current user's role-aware dashboard home and avoid exposing school navigation to recruiter/external-student accounts.
- Wraps the app in `WorkingContextProvider` and guards school-scoped routes via `GuardedModuleContent` + `CONTEXT_REQUIRED_SEGMENTS` (an allowlist — extend it for new school-scoped modules; never make it a denylist or account/settings/site/checkout could be blocked). The guard applies to both desktop and mobile main content.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
