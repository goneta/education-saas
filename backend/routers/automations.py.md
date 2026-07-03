# automations.py

## Purpose
- Staff automations hub (`/automations`): POST /fee-reminders/run (admin/accountant/direction; configurable level2/level3/cooldown days) + GET /fee-reminders/history. Runs are idempotent so they can be triggered manually or by an external cron.

## Verification
- `python -m pytest backend/test_fee_reminders.py`
- Automation C: `POST /parent-digest/run` (days, grade_alert_threshold, absence_alert_count) + `GET /parent-digest/history` (NotificationHistory rows with event_type parent.digest / parent.alert.*). Same admin gate + Super-Admin school_id resolution as fee reminders.
- Automation D (1/n): `POST /absence-followup/run` (days) — parent message per unfollowed absence; `POST /anomaly-digest/run` (days, unpaid_threshold) — one staff brief per window; `GET /notifications/history?event_type=` — generic automation-notification history reused by the cards.
- Automation D (2/n): `GET /rentree/preview` (dry-run plan) + `POST /rentree/run` (body: new_year_name/start_date/end_date) — year rollover; gated to SUPER_ADMIN/SCHOOL_ADMIN/DIRECTION only (RENTREE_ROLES, accountant excluded).
