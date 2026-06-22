# school_model_templates.py

## Purpose

- Owns the six system school-model templates and idempotent assignment-level seeding.
- Creates model-scoped academic years, classes, subjects, programs, fees, periods, diplomas, certifications, and assessment types.

## Contract

- System defaults are marked with `is_system_default`.
- Existing rows are never deleted or overwritten.
- Re-running a seed for the same assignment is idempotent.
