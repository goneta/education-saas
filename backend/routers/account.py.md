# account.py

## Source File

- `backend/routers/account.py`

## Purpose

- Exposes authenticated account preferences, user notifications, cart management, and checkout initiation endpoints.
- Supports saved light/dark theme preference, unread notification count, cart item CRUD, and checkout routing to platform or school payment records.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Cart and notification operations must stay user-scoped.
- Checkout must preserve payment separation: platform items go to platform payments; school items go to school payments.
- Mutations should remain auditable.

## Verification

- `python -m py_compile backend\routers\account.py`
- Import smoke check: `python -c "import backend.main as m; print(m.app.title)"`
