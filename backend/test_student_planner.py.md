# test_student_planner.py — Tests for the study planner + homework reminders

## Coverage

- Study plan compiles assessments, pending homework, the three chronological
  revision steps (overview→practice→final_review) and the class timetable.
- Submitted homework disappears from the plan; a parent reads a linked child's
  plan via student_id; an unlinked student_id → 403.
- Homework reminders: D-3 bucket resolved from the due date, submitted student
  skipped, rerun sends nothing (`skipped_sent`), far-future due dates out of
  scope; teacher → 403 on both the runner and the study-plan endpoint.

## Pattern

In-memory SQLite (StaticPool) + direct router/service calls, same fixtures as
the other automation tests.
