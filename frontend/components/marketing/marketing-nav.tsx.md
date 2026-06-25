# marketing-nav.tsx

## Source File

- `frontend/components/marketing/marketing-nav.tsx`

## Purpose

- React/Next.js TypeScript component for public marketing navigation, including the public TeducAI Emploi entry point.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Public navigation, session-aware actions, and mobile controls remain readable in both light and dark themes.
- Dark mode uses a solid dark top bar, white menu text, and the inherited white TeducAI logo treatment.
- The authenticated Dashboard action must use role-aware routing instead of always linking to the school dashboard.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
