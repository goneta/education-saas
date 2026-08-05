# 20260805_0055_reference_items.py
## Source File
- `alembic/versions/20260805_0055_reference_items.py`
## Purpose
- Creates `reference_items` (generic hierarchical referential: category, code,
  name, sort_order, is_active, school_id NULL=global / set=local, unique
  (category, code, school_id)) and SEEDS the global TeducAI lists: school_type,
  fee_type, room_type, building_type, leave_type, evaluation_type,
  document_type, sanction_type, reward_type (French labels). school_level keeps
  the existing SchoolLevel referential as its global source. Idempotent (table
  presence + per-code seed check); inline column FKs (SQLite-friendly).
## Verification
- `python -m alembic upgrade head`
