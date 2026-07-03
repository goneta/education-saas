# absence_followup.py — Absence follow-up automation (automation D)

## Purpose

`run_absence_followup(db, school_id, current_user, *, days=2, limit=500)`
auto-drafts and sends the parent message for every recent ABSENT attendance
record: notification via `automation.record_notification`
(`event_type="absence.followup"`) addressed to the linked parent account
(message in the parent's `UserPreference.language`, fr/en/es/sw templates,
subject name from the timetable slot included when available), plus a queued
`SmsMessage` (`event_type="absence_followup"`) when the student profile has a
parent phone.

## Idempotence

Each `Attendance` row is followed up at most once: the runner skips rows that
already have an `absence.followup` notification with
`source_type="attendance"`, `source_id=<attendance.id>`. Safe to run after
class, daily, or via cron. Rows without any parent contact are counted in
`skipped_no_contact`. Returns
`{scanned, notified, sms_queued, skipped_done, skipped_no_contact}`.

## Verification

- `python -m pytest backend/test_absence_anomaly.py`
