# test_class_room_rules.py
## Purpose
- #6 smart class/room rules: room capacity guard blocks an oversized class (409) and no-ops for roomier/unknown/no-capacity rooms; `/education/classes/{id}/students` returns count + age + sex.
## Verification
- `python -m pytest backend/test_class_room_rules.py`
