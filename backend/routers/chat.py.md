# chat.py

## Source File

- `backend/routers/chat.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Exposes the role-aware Agent IA chat endpoint, enforcing RBAC, tenant scope, AI credit checks, configured provider calls, usage logging, and audit trails.
- Supplies the active organization, school model, and academic year to providers and honors assignment-level AI disablement.
- Accepts both canonical `/chat` and legacy `/chat/` POST paths to avoid proxy redirects that can break JSON parsing in the frontend chat panel.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
