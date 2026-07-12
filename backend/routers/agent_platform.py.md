# agent_platform.py
## Source File
- `backend/routers/agent_platform.py`
## Purpose
- `/agents` API: `GET /agents/capabilities` (role-filtered agent list +
  providers_configured) and `POST /agents/chat` (SSE stream of the normalized
  agent events; history round-trips via the `done` event's history field).
  AgentContext is built ONLY from the authenticated user (tenant + role never
  client-supplied).
## Verification
- `python -m pytest backend/test_agent_platform.py`
