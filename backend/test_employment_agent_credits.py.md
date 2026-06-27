# test_employment_agent_credits.py

## Purpose

- Verifies the `/employment/agent` endpoint records a usage log (`module_name="employment_agent"`, status successful, credits >= 1) and charges the caller's wallet with a matching usage transaction, so the employment AI agent is metered like the dashboard chat rather than free.

## Verification

- `python -m pytest backend/test_employment_agent_credits.py`
