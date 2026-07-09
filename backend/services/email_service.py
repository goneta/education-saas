"""Transactional e-mail sender (SMTP).

Provider-agnostic SMTP mailer configured entirely from environment variables so
no credential ever lives in the repo. Defaults target Google Workspace / Gmail
(smtp.gmail.com, STARTTLS 587), but any SMTP server works.

Env vars (see .env.example):
  SMTP_HOST        - default "smtp.gmail.com"
  SMTP_PORT        - default 587
  SMTP_SECURITY    - "starttls" (587, default) or "ssl" (465)
  SMTP_USERNAME    - login (also the default From address)
  SMTP_PASSWORD    - password / app-password (NEVER committed)
  SMTP_FROM        - From address (defaults to SMTP_USERNAME)
  SMTP_FROM_NAME   - display name (default "TeducAI")

If the required vars are absent the mailer is "not configured": callers get a
clear failure (mapped to HTTP 503) and nothing is ever faked.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable, Optional, Sequence


class EmailNotConfigured(RuntimeError):
    """Raised when SMTP settings are missing."""


class EmailSendError(RuntimeError):
    """Raised when the SMTP server rejects or the send otherwise fails."""


def _cfg() -> dict:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    security = (os.getenv("SMTP_SECURITY") or "starttls").lower()
    default_port = 465 if security == "ssl" else 587
    port = int(os.getenv("SMTP_PORT", str(default_port)))
    from_addr = os.getenv("SMTP_FROM") or username
    from_name = os.getenv("SMTP_FROM_NAME", "TeducAI")
    return {
        "host": host, "port": port, "security": security,
        "username": username, "password": password,
        "from_addr": from_addr, "from_name": from_name,
    }


def is_configured() -> bool:
    c = _cfg()
    return bool(c["host"] and c["username"] and c["password"] and c["from_addr"])


def _normalize_recipients(to: Sequence[str] | str) -> list[str]:
    items = [to] if isinstance(to, str) else list(to)
    seen, out = set(), []
    for r in items:
        r = (r or "").strip()
        if r and r.lower() not in seen:
            seen.add(r.lower())
            out.append(r)
    return out


def send_email(
    to: Sequence[str] | str,
    subject: str,
    text_body: str,
    *,
    html_body: Optional[str] = None,
    attachments: Optional[Iterable[tuple]] = None,
) -> dict:
    """Send an e-mail. attachments = iterable of (filename, bytes, maintype, subtype)."""
    if not is_configured():
        raise EmailNotConfigured(
            "SMTP is not configured. Set SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD in the environment."
        )
    recipients = _normalize_recipients(to)
    if not recipients:
        raise EmailSendError("No recipient address provided.")

    c = _cfg()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f'{c["from_name"]} <{c["from_addr"]}>'
    msg["To"] = ", ".join(recipients)
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    for att in (attachments or []):
        filename, content, maintype, subtype = att
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    try:
        if c["security"] == "ssl":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(c["host"], c["port"], context=context, timeout=30) as server:
                server.login(c["username"], c["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(c["host"], c["port"], timeout=30) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(c["username"], c["password"])
                server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:  # network / auth / protocol
        raise EmailSendError(f"E-mail delivery failed: {exc}") from exc

    return {"sent": True, "recipients": recipients}
