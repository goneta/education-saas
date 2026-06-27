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
- The `/portal` endpoint restricts student and parent callers to their own student set (own profile, or active `ParentStudentLink` children). An empty set resolves to a `[-1]` sentinel so an unlinked parent or profile-less student sees nothing — never the whole school — and cannot target another student via `student_id`. Only staff with `files:read` get the school-wide view.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
