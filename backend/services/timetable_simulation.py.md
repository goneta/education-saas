# timetable_simulation.py

## Source File

- `backend/services/timetable_simulation.py`

## Purpose

- Explainable AI and what-if simulation for timetables. `explain_candidate` turns an optimiser candidate's score breakdown into plain statements; `simulate` re-runs the optimiser under a modified scenario and reports the impact vs baseline.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Scenarios: `teacher_absent` ({teacher_id}) excludes a teacher and reports uncovered sessions; `extra_working_day` ({day}) adds a day and reports the gain. Both compare a baseline best candidate to the scenario best candidate via `timetable_optimizer.generate_candidates` overrides — no persistence.
- Add a scenario by extending `simulate` and the optimiser overrides; keep results explainable (human-readable `impact`/`explanation`).

## Verification

- python -m py_compile backend\services\timetable_simulation.py; python -m pytest backend/test_timetable_simulation.py
