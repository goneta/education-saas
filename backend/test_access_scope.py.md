# test_access_scope.py
## Source File
- `backend/test_access_scope.py`
## Purpose
- Lot 1 of the audit remediation. PRIV-01: a learner and a parent see only their
  own / their child's discipline records — the classmate's record is invisible in
  the list, **not fetchable by id**, not reachable through `?student_id=` and
  absent from the CSV export; staff keep the full school view. Boarding is row
  scoped while Exams and Activities stay school-wide (no personal data) with
  writes still staff-only; Health stays administration-only even for the student
  concerned. PRIV-02: the `visible_student_ids` / `can_view_student` rules,
  including the "parent with no link sees nothing" case. SEC-07: a CV photo is
  public only with the full opt-in chain.
## Verification
- `python -m pytest backend/test_access_scope.py` (5 green).
