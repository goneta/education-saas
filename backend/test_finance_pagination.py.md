# test_finance_pagination.py
## Source File
- `backend/test_finance_pagination.py`
## Purpose
- Lot 6 (PERF-07 + the bug it uncovered). Proves `GET /finance/cash-journal`
  answers 200 with correct totals — it used to answer **HTTP 500**: the handler
  called `list_payments(...)` with 7 positional arguments against an
  11-parameter signature, so `db` landed in `school_model_assignment_id` and the
  real `db` stayed a `Depends` object. The cashier's daily till-closing screen
  was broken and no test covered it.
- Also covers `/finance/reports` (aggregation still sees every row) and the new
  pagination of `/finance/payments`: default stays unbounded (no consumer
  breaks), `X-Total-Count` publishes the real total, `skip`/`limit` page without
  overlap, ordering stays newest-first, and the hard cap truncates only with an
  explicit `X-Truncated` header — never silently.
## Verification
- `python -m pytest backend/test_finance_pagination.py` (4 green).
