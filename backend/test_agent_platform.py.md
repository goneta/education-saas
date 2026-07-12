# test_agent_platform.py
## Source File
- `backend/test_agent_platform.py`
## Purpose
- Capabilities role filtering (teacher vs cashier); provider fallback order
  (priority asc, inactive excluded) + no-key → no model, never a fake client;
  agent-graph handoffs respect role permissions (student: no Finance;
  accountant: no Tutor); streaming errors cleanly when no provider configured.
## Verification
- `python -m pytest backend/test_agent_platform.py` (4 green).
