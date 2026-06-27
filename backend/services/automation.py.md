# automation.py

## Source File

- `backend/services/automation.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It contains reusable backend business or integration logic.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Automated invoices, outstanding balances, and payment cash-journal rows inherit the fee's school-model assignment.
- `is_overdue(due_date)` is the shared, timezone-safe way to compare a fee/invoice due date against now; it normalizes timezone-aware datetimes (e.g. from an ISO `Z`-suffixed payload) before comparing against the module's naive UTC clock. Other modules (e.g. `backend/routers/finance.py`) should call `automation.is_overdue` instead of comparing `due_date` directly, to avoid `TypeError: can't compare offset-naive and offset-aware datetimes`.

## Verification

- python -m py_compile backend\services\<module>.py; run targeted backend tests when available
# Enrollment scoping

Invoices generated from student fees inherit `student_enrollment_id`, preserving financial isolation when one learner has multiple active schools or training contexts.
