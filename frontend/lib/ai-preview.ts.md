# ai-preview.ts

## Source File

- `frontend/lib/ai-preview.ts`

## Purpose

- Normalizes AI chat structured outputs into Markdown for the dashboard Preview panel, including arrays as tables/lists and nested objects as readable sections.

## DOX Scope

- Nearest contract: `frontend/lib/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep the helper framework-safe and free of browser-only APIs.
- Preserve safe Markdown escaping for table cells.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint lib/ai-preview.ts"`
