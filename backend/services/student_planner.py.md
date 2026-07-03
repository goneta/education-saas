# student_planner.py — Study planner + homework reminders (automation D, students)

## build_study_plan(db, profile, *, horizon_days=21)

Pure read, computed on demand from the student's REAL data:
- upcoming `Assessment` rows of the student's class (with subject names);
- pending homework = PUBLISHED `Assignment` rows with a future due date and
  no `AssignmentSubmission` from this student;
- the class `Timetable` (day/start/end/subject) for context;
- derived spaced-revision slots per assessment: D-5 overview (30 min),
  D-2 practice (45 min), D-1 final review (60 min), chronologically sorted
  (`REVISION_STEPS` is the single tuning point).

## run_homework_reminders(db, school_id, current_user, *, limit=1000)

Spaced-repetition nudges at the D-7 / D-3 / D-1 buckets (`REMINDER_BUCKETS`)
to every active student of the assignment's class who has NOT submitted.
Idempotent per (assignment, student, bucket): the bucket is part of the event
type (`homework.reminder.d7|d3|d1`) checked against NotificationHistory with
`source_type="assignment"`, so daily cron runs never double-send. Returns
`{assignments, reminders, skipped_sent, skipped_submitted}`.

## Verification

- `python -m pytest backend/test_student_planner.py`
