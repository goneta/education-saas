# anomaly_digest.py — Weekly anomaly brief for staff (automation D)

## Purpose

`run_anomaly_digest(db, school_id, current_user, *, days=7, spike_factor=1.5,
spike_floor=5, unpaid_threshold=0.3)` computes three deterministic operational
anomalies and records ONE brief (`event_type="anomaly.digest"`) to the
triggering administrator:

1. **Absence spike** — absences+lates this window vs the previous same-length
   window (flag when current >= spike_factor x previous and >= spike_floor).
2. **Unpaid ratio** — outstanding (billed minus successful payments on
   PENDING/PARTIAL/OVERDUE fees) over total billed (flag above
   `unpaid_threshold`).
3. **Class-size imbalance** — min/max headcount across classes with students
   via `StudentProfile.current_class_id` (flag when max >= 2 x min).

No AI provider needed — metrics are pure DB computations, so the digest works
in every deployment (the "AI brief" phrasing upgrade can plug into
`ai_service` later without changing the contract).

## Idempotence

One brief per (school, window): if an `anomaly.digest` notification exists for
the school within the window, the run returns `{skipped_cooldown: True}`.
Safe to cron weekly.

## Verification

- `python -m pytest backend/test_absence_anomaly.py`
