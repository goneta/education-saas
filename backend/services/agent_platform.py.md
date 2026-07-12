# agent_platform.py
## Source File
- `backend/services/agent_platform.py`
## Purpose
- Multi-agent platform foundation on the OpenAI Agents SDK (openai-agents 0.18):
  Coordinator + Academic + Student-Tutor + Finance agents with role-filtered
  handoffs; 4 tenant-scoped RBAC tools (search_students, lookup_grades,
  lookup_attendance, lookup_invoices); provider fallback from the EXISTING
  AIProvider registry (priority asc, decrypt_secret, base_url per provider →
  OpenAIChatCompletionsModel over AsyncOpenAI); credit-gated via ai_credits;
  `stream_conversation` yields normalized events (start/delta/tool/handoff/done
  with to_input_list history/error) and retries down the provider list on any
  failure (automatic fallback). No provider → clear error, never faked.
## Local Contracts
- Lazy SDK imports; `_tools()` injects RunContextWrapper into module globals
  (stringified annotations). Tracing disabled when no OPENAI_API_KEY.
- Deploy note: install `openai-agents` with `--no-deps` alongside pinned
  fastapi 0.104 stacks (its transitive mcp/starlette/pydantic pins clash);
  runtime needs only openai + pydantic>=2.10<2.12 + griffe.
## Verification
- `python -m pytest backend/test_agent_platform.py` (4 green).
- Live E2E verified (2026-07-12): invalid OpenAI key (401) triggered automatic fallback to the OpenRouter registry provider; real streamed run completed with Coordinator→Academic handoff, search_students/lookup_grades/lookup_attendance tool executions on seeded data, 85 text deltas, credit deduction. Delta filter now passes ONLY ResponseTextDeltaEvent (function-call argument fragments previously leaked into the visible stream).
