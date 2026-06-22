# test_multi_school_context.py

## Purpose

- Verifies assignment-level default seeding, idempotency, context switching, class isolation between models, rejection of a foreign school's assignment, and owner creation of a second multi-model school.

## Verification

- `python -m pytest backend/test_multi_school_context.py -q`
