# 20260612_0018_account_cart_theme.py

## Source File

- `alembic/versions/20260612_0018_account_cart_theme.py`

## Purpose

- Adds account UI persistence and commerce support tables:
  - `notification_history.read_at`
  - `user_preferences`
  - `cart_items`
  - `school_memberships`

## DOX Scope

- Nearest contract: `alembic/versions/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep `down_revision` aligned with the migration chain.
- `school_memberships` stores durable school transfer/history records and should not be replaced by destructive user updates.

## Verification

- `python -m alembic heads`
- `python -m alembic upgrade head` when safe to mutate the active database.
