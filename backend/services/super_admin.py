from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import audit, models, security
from . import ai_credits


DEFAULT_SUPER_ADMIN_FULL_NAME = "Kenneth Cisse"
DEFAULT_SUPER_ADMIN_USERNAME = "kenguigocis"
DEFAULT_SUPER_ADMIN_EMAIL = "thunderfammedia@gmail.com"
DEFAULT_SUPER_ADMIN_PASSWORD = "Password65Gh@"
DEFAULT_SUPER_ADMIN_AI_CREDITS = 1_000_000


@dataclass
class SuperAdminBootstrapResult:
    user: models.User
    wallet: models.AIWallet
    created: bool


def bootstrap_password(explicit_password: str | None = None) -> str:
    return explicit_password or os.getenv("TEDUCAI_SUPER_ADMIN_PASSWORD") or DEFAULT_SUPER_ADMIN_PASSWORD


def ensure_super_admin(
    db: Session,
    *,
    password: str | None = None,
    reset_password: bool = True,
) -> SuperAdminBootstrapResult:
    user = db.query(models.User).filter(
        or_(
            models.User.username == DEFAULT_SUPER_ADMIN_USERNAME,
            models.User.email == DEFAULT_SUPER_ADMIN_EMAIL,
        )
    ).first()
    created = user is None

    if created:
        user = models.User(
            username=DEFAULT_SUPER_ADMIN_USERNAME,
            email=DEFAULT_SUPER_ADMIN_EMAIL,
            full_name=DEFAULT_SUPER_ADMIN_FULL_NAME,
            role=models.UserRole.SUPER_ADMIN,
            hashed_password=security.get_password_hash(bootstrap_password(password)),
            is_active=True,
            is_verified=True,
            is_system_account=True,
            school_id=None,
        )
        db.add(user)
        db.flush()
    else:
        user.username = DEFAULT_SUPER_ADMIN_USERNAME
        user.email = DEFAULT_SUPER_ADMIN_EMAIL
        user.full_name = DEFAULT_SUPER_ADMIN_FULL_NAME
        user.role = models.UserRole.SUPER_ADMIN
        user.is_active = True
        user.is_verified = True
        user.is_system_account = True
        user.school_id = None
        if reset_password:
            user.hashed_password = security.get_password_hash(bootstrap_password(password))
        db.add(user)
        db.flush()

    _reset_super_admin_role_assignment(db, user)
    wallet = _ensure_super_admin_wallet(db, user)

    audit.record_audit(
        db,
        action="system.super_admin_bootstrapped",
        current_user=user,
        entity_type="user",
        entity_id=user.id,
        details={
            "username": user.username,
            "email": user.email,
            "created": created,
            "wallet_credits": wallet.balance_credits,
        },
    )
    return SuperAdminBootstrapResult(user=user, wallet=wallet, created=created)


def _reset_super_admin_role_assignment(db: Session, user: models.User) -> None:
    db.query(models.UserRoleAssignment).filter(models.UserRoleAssignment.user_id == user.id).delete()
    db.add(models.UserRoleAssignment(
        user_id=user.id,
        role_key=models.UserRole.SUPER_ADMIN.value,
        school_id=None,
        assigned_by_id=user.id,
    ))
    db.flush()


def _ensure_super_admin_wallet(db: Session, user: models.User) -> models.AIWallet:
    wallet = ai_credits.wallet_for_user(db, user)
    if wallet.balance_credits < DEFAULT_SUPER_ADMIN_AI_CREDITS:
        before = wallet.balance_credits
        wallet.balance_credits = DEFAULT_SUPER_ADMIN_AI_CREDITS
        wallet.total_purchased_credits = max(wallet.total_purchased_credits, DEFAULT_SUPER_ADMIN_AI_CREDITS)
        wallet.daily_credit_limit = None
        wallet.monthly_credit_limit = None
        wallet.status = "active"
        db.add(models.AICreditTransaction(
            wallet_id=wallet.id,
            user_id=user.id,
            school_id=None,
            transaction_type="admin_adjustment",
            credits_amount=wallet.balance_credits - before,
            balance_before=before,
            balance_after=wallet.balance_credits,
            description="Bootstrap super admin AI wallet",
        ))
    else:
        wallet.daily_credit_limit = None
        wallet.monthly_credit_limit = None
        wallet.status = "active"
    db.add(wallet)
    db.flush()
    return wallet
