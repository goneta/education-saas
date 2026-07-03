# test_parent_actions.py — Tests for parent one-tap actions (automation D)

## Coverage

- A linked parent justifies a child's absence in one tap: status ABSENT ->
  EXCUSED, traceable remark appended, and the recording teacher receives the
  `absence.justified` notification (source = attendance row).
- Guards: second tap on an excused row -> 409; unlinked parent -> 403;
  non-parent roles -> 403; unknown attendance -> 404; a PRESENT row cannot
  be justified (409).

## Pattern

In-memory SQLite (StaticPool) + direct router calls; fixture builds the full
attendance chain (class -> subject -> timetable -> attendance with
recorded_by teacher) plus the ParentStudentLink.
