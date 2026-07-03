# page.tsx (System - Automations)

## Purpose
- Automations hub UI: unpaid-fee reminders section (threshold inputs, Run now, result summary cards, cron hint, reminder history table). i18n `automations` namespace (FR/EN/ES/SW). Extended by later increments (parent digest, ...).
- Automation C: second card "Resume hebdomadaire aux parents" — window/threshold inputs, run-now, summary (families/digests/average alerts/attendance alerts/skipped), history table of parent.digest + parent.alert.* notifications (badge distinguishes digest vs alert; message shown as row title tooltip).
- Automation D (1/n): cards 3-4 — "Suivi des absences" (window input, run, scanned/notified/SMS/skipped summary, notification history) and "Brief anomalies" (window + unpaid-threshold inputs, run, anomalies/absences/unpaid-ratio/headcount summary or cooldown banner, expandable brief history via <details>). Both use GET /automations/notifications/history?event_type=.
- Automation D (2/n): card 5 "Assistant de rentree" — preview button (promotions table, leavers/unmapped/fee counts), new-year name + start/end date inputs, run button with window.confirm, result summary (promoted/archived/unmapped/schedules cloned), guard-rail hint.
- Automation D (3/n): card 6 "Rappels de devoirs" — run-now + assignments/reminders/already-submitted/skipped summary (inserted before the rentree card).
