# academics.py

## Source File

- `backend/services/academics.py`

## Purpose

- `compute_gpa(db, student_id, term_id=None)`: weighted GPA over existing `Grade`/`Assessment` data (score vs max_score, weighted by assessment weight/coefficient). Returns percentage, average/20, GPA/4, total weight and a per-subject breakdown.

## Local Contracts

- Pure computation; no new tables (grades remain the single source of truth). Skips assessments with non-positive max_score; clamps fractions to [0,1].

## Verification

- `python -m pytest backend/test_academics.py`
