# test_absence_anomaly.py — Tests for absence follow-up + anomaly digest (automation D)

## Coverage

- Absence follow-up: parent notified (subject name in the message), SMS queued
  when a parent phone is on file; rerun skips already-followed rows
  (`skipped_done`); PRESENT rows are not scanned; students without any parent
  contact land in `skipped_no_contact`.
- Anomaly digest: a school with an absence spike, 100% unpaid ratio and a 4-vs-1
  class imbalance flags all 3 anomalies and notifies the admin; a rerun within
  the window returns `skipped_cooldown`; a quiet school still gets a "no
  anomaly" brief.
- Endpoint RBAC: teacher → 403 on both `/automations/absence-followup/run` and
  `/automations/anomaly-digest/run`; the generic
  `/automations/notifications/history?event_type=` endpoint returns the brief.

## Pattern

In-memory SQLite (StaticPool) + direct router/service calls, same fixture
style as the other automation tests.
