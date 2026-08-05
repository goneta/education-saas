"""Self-service password reset (audit SEC-05).

Before this module the only way out of a forgotten password was an
administrator — untenable at the start of a school year when thousands of
parents and students log in for the first time.

Doctrine:
- **No account enumeration**: `request_reset` never reveals whether the address
  exists; the caller always gets the same answer.
- **Only a hash is stored**: the database never holds a usable reset link.
- **One shot, short lived**: a token is valid `RESET_TOKEN_TTL_MINUTES` (default
  60) and is consumed on use; every other pending token of the user is
  invalidated at the same time.
- **Sessions are revoked**: a completed reset bumps `token_version`, so JWTs
  issued before the reset (possibly to the attacker) stop working.
- **Nothing is faked**: if SMTP is not configured the caller gets an explicit
  error instead of a silent no-op — see `routers/auth.py`.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models, security
from . import email_service

logger = logging.getLogger("teducai.password_reset")

RESET_TOKEN_TTL_MINUTES = int(os.getenv("PASSWORD_RESET_TTL_MINUTES", "60"))
MAX_ACTIVE_REQUESTS_PER_HOUR = int(os.getenv("PASSWORD_RESET_MAX_PER_HOUR", "5"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def reset_url(token: str) -> str:
    base = (os.getenv("APP_URL") or os.getenv("DOCUMENT_VERIFY_BASE_URL") or "https://teducai.com").rstrip("/")
    return f"{base}/reset-password?token={token}"


def _recent_request_count(db: Session, user_id: int) -> int:
    since = _now() - timedelta(hours=1)
    return (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.user_id == user_id,
            models.PasswordResetToken.created_at >= since,
        )
        .count()
    )


def create_token(db: Session, user: models.User, *, ip_address: Optional[str] = None) -> Optional[str]:
    """Issue a reset token. Returns None when the user is rate-limited."""
    if _recent_request_count(db, user.id) >= MAX_ACTIVE_REQUESTS_PER_HOUR:
        logger.warning("Password reset throttled for user %s", user.id)
        return None
    token = secrets.token_urlsafe(32)
    db.add(models.PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=_now() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
        requested_ip=ip_address,
    ))
    db.flush()
    return token


def send_reset_email(user: models.User, token: str, *, language: str = "fr") -> None:
    """Deliver the reset link. Raises EmailNotConfigured / EmailSendError —
    callers decide how to surface it; nothing is ever silently swallowed."""
    link = reset_url(token)
    minutes = RESET_TOKEN_TTL_MINUTES
    if language.startswith("en"):
        subject = "TeducAI — reset your password"
        body = (
            f"Hello {user.full_name or ''},\n\n"
            f"A password reset was requested for your TeducAI account.\n"
            f"Open the link below to choose a new password (valid for {minutes} minutes):\n\n"
            f"{link}\n\n"
            "If you did not request this, you can ignore this message: your password stays unchanged.\n"
        )
    else:
        subject = "TeducAI — réinitialisation de votre mot de passe"
        body = (
            f"Bonjour {user.full_name or ''},\n\n"
            f"Une réinitialisation de mot de passe a été demandée pour votre compte TeducAI.\n"
            f"Ouvrez le lien ci-dessous pour choisir un nouveau mot de passe "
            f"(valable {minutes} minutes) :\n\n"
            f"{link}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message : "
            "votre mot de passe reste inchangé.\n"
        )
    email_service.send_email(user.email, subject, body)


def consume_token(db: Session, token: str) -> Optional[models.User]:
    """Validate and burn a reset token. Returns the user, or None when the token
    is unknown, already used or expired."""
    row = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.token_hash == hash_token(token))
        .first()
    )
    if not row or row.used_at is not None:
        return None
    expires_at = row.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at is not None and expires_at < _now():
        return None
    user = db.query(models.User).filter(models.User.id == row.user_id).first()
    if not user:
        return None
    row.used_at = _now()
    # Any other pending token of this user is now worthless.
    for other in (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.user_id == user.id,
            models.PasswordResetToken.used_at == None,  # noqa: E711
        )
        .all()
    ):
        other.used_at = _now()
    return user


def apply_new_password(db: Session, user: models.User, new_password: str) -> None:
    """Set the new password, unlock the account and revoke existing sessions."""
    security.validate_password_strength(new_password)
    user.hashed_password = security.get_password_hash(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.token_version = (user.token_version or 0) + 1  # every old JWT dies here
    db.flush()
