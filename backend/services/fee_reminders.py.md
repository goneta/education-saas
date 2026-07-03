# fee_reminders.py

## Purpose
- Auto-relance des impayes: scans pending/partial/overdue fees past due date, computes true outstanding (amount - successful payments), sends escalating reminders (L1 gentle / L2 firm / L3 urgent + admin escalation), queues parent SMS when a phone is on file, and records a FeeReminder row per send (anti-spam: cooldown + never repeat a level). Idempotent; no background worker needed.

## Verification
- `python -m pytest backend/test_fee_reminders.py`
