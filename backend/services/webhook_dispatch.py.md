# webhook_dispatch.py
## Source File
- `backend/services/webhook_dispatch.py`
## Purpose
- Outbound webhook sender (audit OPS-02). `emit_event` queued deliveries but
  nothing ever sent them: rows stayed `pending` while the API & Integrations page
  advertised working integrations. `dispatch_pending(db, limit=)` sends every DUE
  delivery; `deliver_one` signs the exact body with HMAC-SHA256 of the endpoint
  secret (`X-TeducAI-Signature`), marks `delivered` on 2xx, and on failure backs
  off exponentially (2, 4, 8… minutes) until `max_attempts` before marking
  `failed` with the reason in `last_error` — never silently dropped.
## Local Contracts
- Pull runner driven by cron (`POST /extensibility/deliveries/dispatch`), like the
  other TeducAI automations — no broker, no daemon. Idempotent and safe to run
  often: only pending rows whose `next_retry_at` has come are sent.
## Verification
- `python -m pytest backend/test_report_cards.py` (delivery signature, backoff,
  definitive failure and skipped-backoff cases).
