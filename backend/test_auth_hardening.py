"""Lot 2 — audit SEC-03 / SEC-04 / SEC-05 : durcissement de l'authentification."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, security, security_middleware
from backend.services import password_reset


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _user(db, password="OriginalPass123!"):
    tag = uuid.uuid4().hex[:6]
    user = models.User(
        email=f"u_{tag}@x.com", hashed_password=security.get_password_hash(password),
        full_name="U", role=models.UserRole.TEACHER, is_active=True, token_version=3,
    )
    db.add(user); db.commit()
    return user


class _FakeRequest:
    """Minimal Request stand-in for the rate-limit key helper."""
    def __init__(self, peer, forwarded=None, path="/auth/token"):
        self.client = type("C", (), {"host": peer})()
        self.headers = {"x-forwarded-for": forwarded} if forwarded else {}
        self.url = type("U", (), {"path": path})()


# --- SEC-03: X-Forwarded-For is only trusted behind a declared proxy ---------

def test_forwarded_header_is_ignored_from_an_untrusted_peer(monkeypatch):
    monkeypatch.setattr(security_middleware, "TRUSTED_PROXY_IPS", {"10.0.0.1"})
    spoofing = _FakeRequest("203.0.113.9", forwarded="1.2.3.4")
    # The attacker's own address is counted, so rotating the header no longer
    # buys a fresh rate-limit bucket.
    assert security_middleware.client_ip(spoofing) == "203.0.113.9"
    assert security_middleware.client_ip(_FakeRequest("203.0.113.9", forwarded="5.6.7.8")) == "203.0.113.9"


def test_forwarded_header_is_honored_behind_a_trusted_proxy(monkeypatch):
    monkeypatch.setattr(security_middleware, "TRUSTED_PROXY_IPS", {"10.0.0.1"})
    request = _FakeRequest("10.0.0.1", forwarded="1.2.3.4, 10.0.0.1")
    assert security_middleware.client_ip(request) == "1.2.3.4"
    # No header behind the proxy: fall back to the peer.
    assert security_middleware.client_ip(_FakeRequest("10.0.0.1")) == "10.0.0.1"


# --- SEC-05: password reset --------------------------------------------------

def test_reset_token_is_single_use_and_revokes_sessions():
    db = _session()
    user = _user(db)
    original_version = user.token_version

    token = password_reset.create_token(db, user, ip_address="203.0.113.5")
    db.commit()
    assert token and len(token) > 20

    # Only the hash is stored — the database never holds a usable link.
    stored = db.query(models.PasswordResetToken).filter_by(user_id=user.id).first()
    assert stored.token_hash == password_reset.hash_token(token)
    assert token not in stored.token_hash

    consumed = password_reset.consume_token(db, token)
    assert consumed is not None and consumed.id == user.id
    password_reset.apply_new_password(db, consumed, "BrandNewPass123!")
    db.commit()

    assert security.verify_password("BrandNewPass123!", user.hashed_password)
    assert user.token_version == original_version + 1   # old JWTs are dead
    assert user.failed_login_attempts == 0 and user.locked_until is None

    # One shot: the same token cannot be replayed.
    assert password_reset.consume_token(db, token) is None


def test_reset_token_rejects_unknown_expired_and_sibling_tokens():
    db = _session()
    user = _user(db)
    assert password_reset.consume_token(db, "not-a-real-token") is None

    expired = password_reset.create_token(db, user)
    row = db.query(models.PasswordResetToken).filter_by(token_hash=password_reset.hash_token(expired)).first()
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    assert password_reset.consume_token(db, expired) is None

    # Consuming one token invalidates the user's other pending tokens.
    first = password_reset.create_token(db, user)
    second = password_reset.create_token(db, user)
    db.commit()
    assert password_reset.consume_token(db, second) is not None
    assert password_reset.consume_token(db, first) is None


def test_reset_requests_are_throttled(monkeypatch):
    db = _session()
    user = _user(db)
    monkeypatch.setattr(password_reset, "MAX_ACTIVE_REQUESTS_PER_HOUR", 2)
    assert password_reset.create_token(db, user) is not None
    assert password_reset.create_token(db, user) is not None
    db.commit()
    assert password_reset.create_token(db, user) is None  # throttled, no new mail


def test_new_password_must_satisfy_the_policy():
    db = _session()
    user = _user(db)
    with pytest.raises(HTTPException) as exc:
        password_reset.apply_new_password(db, user, "weak")
    assert exc.value.status_code == 400
