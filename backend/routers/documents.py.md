# documents.py

## Source File

- `backend/routers/documents.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Receipt, certificate, report-card, and diploma PDFs use the persisted school identity and logo through the shared document header.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
