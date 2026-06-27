# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/ai-agent/page.tsx`

## Purpose

- Mobile dashboard Agent IA route with chat, local Preview view, shared desktop Preview synchronization, print/download actions, and structured AI output normalization.
- Content responses open the preview immediately and reveal progressively via `revealProgressively` (updating both the local and shared desktop preview); the reveal is cancelled on unmount and when a new message arrives.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Use `formatPreviewContent` before rendering backend `data` so structured lists, tables, and analytics objects are readable in Preview mode.
- Backend chat errors must be displayed as clean user-facing messages from `detail`, not raw JSON or HTTP status wrappers.
- Keep the source file and this document in the same directory.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
