# bootstrap.py

## Source File

- `backend/routers/bootstrap.py`

## Purpose

- Exposes a secured bootstrap endpoint for creating or repairing the system super administrator account.
- Requires `SUPER_ADMIN_BOOTSTRAP_TOKEN` and the matching `X-Teducai-Bootstrap-Token` request header.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Do not expose bootstrap endpoints without an environment-backed secret.
- Do not return passwords, password hashes, or secret configuration values.

## Verification

- `python -m py_compile backend\routers\bootstrap.py`
- `python -c "import backend.main as m; print(m.app.title)"`
