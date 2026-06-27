# finance.py

## Source File

- `backend/routers/finance.py`

## Purpose

- Exposes tenant-scoped fee, cash journal, receipt, report, closure, forecast, and payment APIs with method/reference capture and audit logging.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Fee and fee-schedule creation/listing are scoped to the validated active school-model assignment.
- `_recalculate_fee_status` uses `automation.is_overdue` rather than comparing `fee.due_date` directly against `datetime.now()`, so a timezone-aware due date never raises a naive/aware comparison error when a fee is updated or paid.
- `/payments` and `/reports` accept active-context scoping by school-model assignment and academic year: explicit query params win, otherwise the `X-School-Model-Assignment-ID` / `X-Academic-Year-ID` headers (injected globally by the frontend) are honoured. Scoping only narrows within the already school-scoped result set; with neither present, reports stay school-wide (backward compatible).

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
# Student enrollment scope

Student fees require an active enrollment in the selected school/model/year and inherit that enrollment ID. Closed academic years reject fee creation unless a valid historical edit grant applies.
