# automations.py

## Purpose
- Staff automations hub (`/automations`): POST /fee-reminders/run (admin/accountant/direction; configurable level2/level3/cooldown days) + GET /fee-reminders/history. Runs are idempotent so they can be triggered manually or by an external cron.

## Verification
- `python -m pytest backend/test_fee_reminders.py`
