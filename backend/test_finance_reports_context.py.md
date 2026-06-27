# test_finance_reports_context.py

## Purpose

- Verifies `/finance/reports` can be scoped by academic year (matching year keeps fees, a different year excludes them) and by school-model assignment.
- Verifies the same scoping works through the `X-Academic-Year-ID` context header the frontend injects globally.
- Verifies the default (no context) report stays school-wide so existing behaviour is unchanged.

## Verification

- `python -m pytest backend/test_finance_reports_context.py`
