# enterprise.py

## Source File

- `backend/routers/enterprise.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
- Correctif seconde passe: `/enterprise/direction-dashboard/advanced` renvoyait **500** (jointure ambigue SQLAlchemy 2.0 avec quatre entites selectionnees). `select_from(Payment)` + clause ON explicite. Detecte par le balayage anti-500 de la surface API.
