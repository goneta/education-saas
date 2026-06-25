# page.tsx

## Source File

- `frontend/app/[locale]/pricing/page.tsx`

## Purpose

- Public TeducAI pricing page for Free, Pro, and Max plan presentation with billing choices and subscription calls to action.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Plan cards, billing options, feature lists, and buttons must stay high contrast in light and dark mode.
- Subscription CTAs route to the localized contact page with the selected plan slug.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
