# ai_automation.py

## Source File

- `backend/routers/ai_automation.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Registers the AI automation agents, including the advanced agents 21-40, routes commands to role-scoped agents, enforces RBAC, consumes AI credits, records audit events, and returns structured automation results.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- `python -m py_compile backend\routers\ai_automation.py`
- `python -c "import backend.main as m; print(m.app.title)"`
