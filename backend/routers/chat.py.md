# chat.py

## Source File

- `backend/routers/chat.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Exposes the role-aware Agent IA chat endpoint, enforcing RBAC, tenant scope, AI credit checks, configured provider calls, usage logging, and audit trails.
- Supplies the active organization, school model, and academic year to providers and honors assignment-level AI disablement.
- Multi-agent: each request is routed to the most qualified of the 41 `services/ai_agents.py` agents and the chosen agent's domain persona is injected into the RBAC context, so the single chat behaves as a coordinated multi-agent system. `/chat/agents` lists the roster with per-user authorization; `/chat/route` returns the routing decision (selected agent, authorized, candidates, handoff). Routing is advisory — per-request permission checks and tenant scoping still apply.
- Accepts both canonical `/chat` and legacy `/chat/` POST paths to avoid proxy redirects that can break JSON parsing in the frontend chat panel.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
