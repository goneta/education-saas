# 20260623_0025_ai_credit_monitoring.py

## Source File

- `alembic/versions/20260623_0025_ai_credit_monitoring.py`

## Purpose

- Adds provider-level AI credit monitoring metadata and a persistent platform AI threshold settings table.

## DOX Scope

- Nearest contract: `alembic/versions/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Provider API keys remain encrypted and are not exposed by the monitoring API.
- The platform settings table stores the Super Admin low-credit threshold and notification toggle.

## Verification

- `python -m alembic heads`
- `python -m alembic upgrade head` when safe for the active database.
