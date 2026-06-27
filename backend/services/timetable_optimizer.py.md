# timetable_optimizer.py

## Source File

- `backend/services/timetable_optimizer.py`

## Purpose

- Generates several conflict-free candidate timetables and scores them (0–100) so an admin can pick the best. In-memory, deterministic per seed.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Hard constraints enforced during placement: class/teacher double-booking and teacher availability (`teacher_available_days` rule). Soft quality (fill rate, balanced heavy subjects, no same-subject-twice-a-day, configured time windows) feeds the score; soft penalties come from the database `TimetableConstraintRule` rows, not hard-coded.
- `Candidate.breakdown` is the explainability seed (Phase 5). `generate_candidates` reads the configurable grid/volume via `timetable_config` and returns candidates best-first.
- Pure/side-effect free: it never persists. Committing a chosen candidate is the router's job (`/timetables/optimize/commit`).

## Verification

- python -m py_compile backend\services\timetable_optimizer.py; python -m pytest backend/test_timetable_optimizer.py
