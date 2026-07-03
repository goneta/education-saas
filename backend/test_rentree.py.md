# test_rentree.py — Tests for the rentrée wizard (automation D)

## Coverage

- Preview: promotion lines (6EME→5EME x3), terminal-level student counted as
  leaver, fee schedule counted for cloning; nothing written.
- Run: new year becomes the single current one; 4 students split 2+2 across
  the two next-level classes (least-filled balancing); `previous_level/
  previous_class` recorded; leaver archived (class cleared, UNASSIGNED,
  account still active); fee schedule cloned onto the new year with the old
  one demoted; `rentree.completed` notification recorded.
- Guards: duplicate year name → 409; end <= start → 422.
- Endpoint RBAC: ACCOUNTANT denied (403) on both preview and run (rentrée is
  SUPER_ADMIN/SCHOOL_ADMIN/DIRECTION only).

## Pattern

In-memory SQLite (StaticPool) + direct service/router calls; SchoolLevel codes
are uuid-suffixed because the referential is globally unique.
