# manage.py

## Source File

- `manage.py`

## Purpose

- Root command dispatcher for operational backend commands.
- Currently supports `python manage.py create_super_admin`, which bootstraps or repairs the TeducAI system super administrator account.

## DOX Scope

- Nearest contract: root `AGENTS.md`
- Keep this documentation understandable together with root AGENTS.md.

## Maintenance Notes

- Add new commands only when they are safe to invoke from a VPS shell and have clear output.
- Do not embed or print real secrets.

## Verification

- `python -m py_compile manage.py`
