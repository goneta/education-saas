# parent_digest.py — Weekly parent digest + threshold alerts (automation C)

## Purpose

`run_parent_digest(db, school_id, current_user, *, days=7, grade_alert_threshold=10.0,
absence_alert_count=3, limit=1000)` compiles, for every active `ParentStudentLink`
of the school, the child's window summary — new grades (+ average /20 normalized by
`Assessment.max_score`), absences/lates (`Attendance` ABSENT/LATE), outstanding fees
(PENDING/PARTIAL/OVERDUE minus successful payments) — into ONE notification per
(parent, child) recorded via `automation.record_notification`
(`event_type="parent.digest"`).

## Threshold alerts (ride along the digest run)

- `parent.alert.average` when the window average is below `grade_alert_threshold`.
- `parent.alert.absences` when absences+lates reach `absence_alert_count`.

## Language

The digest is written in the parent's language: `UserPreference.language`
(fr/en/es/sw, default fr) resolves a `TEMPLATES` block — keep the four locales
in sync when editing wording.

## Idempotence

A (parent, child) pair with a `parent.digest` notification inside the window is
skipped (`skipped_cooldown`), so the runner is safe to re-run or cron weekly.
Returns `{links, digests, grade_alerts, absence_alerts, skipped_cooldown}`.

## Verification

- `python -m pytest backend/test_parent_digest.py`
