# page.tsx (AI Agents chat)
## Source File
- `frontend/app/[locale]/dashboard/ai-agents/page.tsx`
## Purpose
- Streaming multi-agent chat UI over POST /agents/chat (SSE): renders text
  deltas live, a thinking indicator, tool-activity line (Wrench + tool name),
  handoff badges (agent name on the assistant bubble), suggested prompts,
  new-conversation reset; conversation continuity via the `done` event's
  history (result.to_input_list()) round-tripped on the next request.
  GET /agents/capabilities shows role-visible agent chips + the no-provider
  notice. i18n namespace `aiAgents` (FR/EN full, es/sw = EN).
## Verification
- FE build unavailable in sandbox — verified by inspection (balance, casts).
