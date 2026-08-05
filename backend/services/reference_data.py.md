# reference_data.py
## Source File
- `backend/services/reference_data.py`
## Purpose
- ONE generic mechanism for every referential list: GLOBAL items (school_id NULL,
  Super-Admin-only writes, visible to all schools, read-only for them) + LOCAL
  per-school extensions (invisible to other schools). `merged_items` is the single
  list forms display (sorted, deduped by code, `scope: global|school`).
- `CATEGORIES` registry (school_level, school_type, fee_type, room_type,
  building_type, leave_type, evaluation_type, document_type, sanction_type,
  reward_type) — adding a future list = one entry here, permissions/merge/UI
  behavior come for free.
- `school_level` special case: the global part is the EXISTING `SchoolLevel`
  referential (source "levels", managed on /levels — zero duplication); local
  level additions live in reference_items like any category.
## Local Contracts
- Writes: `_resolve_write_scope` — Super Admin -> global (or scope "school" +
  school_id); SCHOOL_ADMIN/DIRECTION -> ALWAYS local to their school; scope
  "global" from a school -> 403 GLOBAL_READONLY_DETAIL. `_load_for_write` — a
  school NEVER updates/deletes a global row (403), nor another school's row.
  Duplicate code in the merged view -> 409. Every mutation audited (`reference.*`).
## Verification
- `python -m pytest backend/test_reference_data.py` (5 green).
