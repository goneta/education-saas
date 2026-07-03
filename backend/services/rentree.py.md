# rentree.py — Rentrée wizard / academic-year rollover (automation D)

## Purpose

One flow that rolls an academic year over, in two phases:

- `plan_rentree(db, school_id)` — pure dry-run: per-level promotions (global
  `SchoolLevel.sort_order` referential x the school's actual classes), leavers
  (students whose next level has no class in this school, including the
  terminal level), unmapped students (class level absent from the referential
  — left untouched), and the current year's `FeeSchedule` rows to clone.
- `run_rentree(db, school_id, current_user, *, new_year_name, start_date,
  end_date)` — executes it: creates the new current `AcademicYear` (previous
  one demoted), promotes each student to the LEAST-FILLED class of the next
  level (live headcount balancing), archives leavers (`previous_level`/
  `previous_class` recorded, `current_class_id` cleared, status UNASSIGNED —
  the User account STAYS ACTIVE so families keep portal/self-documents
  access), clones fee schedules onto the new year (old ones `is_current=False`),
  audits and notifies (`rentree.completed`).

## Guard rails

- 409 when an academic year with the same name already exists for the school
  (double-click / replay protection — the rollover cannot run twice).
- 422 when end_date <= start_date.
- Promotion iterates a snapshot of (profile, old class) pairs, so students
  already in the next level move up exactly one level in the same run.

## Verification

- `python -m pytest backend/test_rentree.py`
