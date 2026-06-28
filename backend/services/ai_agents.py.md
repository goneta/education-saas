# ai_agents.py

## Source File

- `backend/services/ai_agents.py`

## Purpose

- The TeducAI Multi-Agent registry: 41 specialized, security-hardened AI agents (template-adapted). Each agent declares a domain, a gating permission, routing keywords, data sources and a system prompt that embeds the shared security contract. Provides `accessible_agents` (RBAC filter) and `select_agent` (permission-aware routing/orchestration).

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- This registry is the source of truth for chat agent routing; the automation action catalogue in `routers/ai_automation.py` covers the command-center side. Keep `AGENTS` at 41 unique keys.
- Every agent's `system_prompt()` prepends `SECURITY_PREAMBLE` (auth/session/tenant, RBAC/ABAC, zero trust, prompt-injection resistance, masking, GDPR, handoff). Do not remove the preamble when adding agents.
- `select_agent` is LLM-first: it calls `ai_service.route_to_agent` (lazy import, no cycle) to pick an agent, then falls back to deterministic keyword scoring and finally the coordinator. The result includes `method` ("llm" or "keyword"). A `classifier` callable can be injected for tests. It reports `authorized` (RBAC) + `refusal` so callers can deny unauthorized requests, and never raises (a failing/absent provider degrades to keyword routing).
- Routing is advisory: the chat endpoint still enforces per-request permission checks and tenant scoping independently.

## Verification

- python -m py_compile backend\services\ai_agents.py; python -m pytest backend/test_ai_agents.py
