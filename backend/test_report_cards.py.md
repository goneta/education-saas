# test_report_cards.py
## Source File
- `backend/test_report_cards.py`
## Purpose
- Lot 4 of the audit remediation. FONC-01: the bulletin context carries the real
  student/class/term data and the right mention, the document is registered once
  (idempotent regeneration) and `render_pdf` returns a genuine PDF; a term with
  no grades still renders. OPS-02: a delivery is actually sent and HMAC-signed,
  a failing endpoint backs off then fails definitively at max_attempts, and a
  delivery still inside its backoff window is skipped.
## Verification
- `python -m pytest backend/test_report_cards.py` (5 green).
