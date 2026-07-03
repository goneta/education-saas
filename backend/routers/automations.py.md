# automations.py

## Purpose
- Staff automations hub (`/automations`): POST /fee-reminders/run (admin/accountant/direction; configurable level2/level3/cooldown days) + GET /fee-reminders/history. Runs are idempotent so they can be triggered manually or by an external cron.

## Verification
- `python -m pytest backend/test_fee_reminders.py`
- Automation C: `POST /parent-digest/run` (days, grade_alert_threshold, absence_alert_count) + `GET /parent-digest/history` (NotificationHistory rows with event_type parent.digest / parent.alert.*). Same admin gate + Super-Admin school_id resolution as fee reminders.
- Automation D (1/n): `POST /absence-followup/run` (days) — parent message per unfollowed absence; `POST /anomaly-digest/run` (days, unpaid_threshold) — one staff brief per window; `GET /notifications/history?event_type=` — generic automation-notification history reused by the cards.
- Automation D (2/n): `GET /rentree/preview` (dry-run plan) + `POST /rentree/run` (body: new_year_name/start_date/end_date) — year rollover; gated to SUPER_ADMIN/SCHOOL_ADMIN/DIRECTION only (RENTREE_ROLES, accountant excluded).
- Automation D (3/n): `GET /study-plan` (STUDENT/PUPIL self, PARENT via ParentStudentLink) — on-demand revision plan; `POST /homework-reminders/run` (admin) — spaced D-7/D-3/D-1 nudges, idempotent per (assignment, student, bucket).
- Automation D (4/n): `GET /remediation/assessments` (stats listing) + `POST /remediation/{assessment_id}/run` (threshold_ratio, language) — EDUCATOR_ROLES (teacher included); generation is AI-credit-gated in the service.
- Automation D (5/n): `GET /explain-grade/grades` + `POST /explain-grade/{grade_id}/run?language=` — student/parent AI grade walk-through; shared `_student_or_linked_child` resolver now serves both study-plan and explain-grade.
