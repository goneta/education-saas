# agent-panel.tsx

## Source File

- `frontend/components/ai-agent/agent-panel.tsx`

## Purpose

- Dashboard AI Agent panel for chat requests, provider-backed responses, and automatic Preview mode switching when content or structured data is returned.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Chat bubbles, composer, placeholder, attachments, microphone, send action, and collapse control remain readable in dark mode.
- Structured AI response objects must be normalized through `formatPreviewContent` before writing to the shared Preview panel.
- Backend chat errors must be displayed as clean user-facing messages from `detail`, not as raw HTTP/JSON wrappers.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
