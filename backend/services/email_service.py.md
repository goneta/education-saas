# email_service.py
## Source File
- `backend/services/email_service.py`
## Purpose
- Provider-agnostic SMTP mailer configured entirely from environment variables
  (no credential in the repo). Defaults to Google Workspace / Gmail
  (smtp.gmail.com, STARTTLS 587); SSL 465 supported.
## Local Contracts
- Env: SMTP_HOST, SMTP_PORT, SMTP_SECURITY (starttls|ssl), SMTP_USERNAME,
  SMTP_PASSWORD, SMTP_FROM, SMTP_FROM_NAME. `is_configured()` gates use.
- `send_email(to, subject, text_body, html_body=None, attachments=[(name,bytes,maintype,subtype)])`
  raises `EmailNotConfigured` (→ HTTP 503) or `EmailSendError` (→ HTTP 502).
  Never faked — no local fallback.
## Verification
- `python -m pytest backend/test_billing.py -k email` (mailer mocked).
