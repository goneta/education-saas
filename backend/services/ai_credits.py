from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import audit, models


INSUFFICIENT_AI_CREDITS = "Votre solde de crédits IA est insuffisant. Veuillez acheter des crédits pour continuer à utiliser l’Agent IA."
AI_CREDIT_LIMIT_REACHED = "La limite de credits IA configuree pour votre compte ou votre etablissement est atteinte. Veuillez contacter votre administrateur."


def platform_payment_reference(prefix: str = "TPL") -> str:
    return f"{prefix}-{datetime.utcnow():%Y%m%d}-{uuid.uuid4().hex[:10].upper()}"


def beneficiary_for_region(country_code: Optional[str], region: Optional[str]) -> str:
    if (region or "").lower() in {"uk", "europe", "uk_europe"} or (country_code or "").upper() in {"GB", "UK", "FR", "ES", "DE", "IT", "BE", "NL", "IE"}:
        return "thunderfam_uk"
    return "thunderfam_ci"


def active_provider(db: Session) -> Optional[models.AIProvider]:
    return db.query(models.AIProvider).filter(models.AIProvider.is_active == True).order_by(models.AIProvider.priority.asc()).first()  # noqa: E712


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 4))


def estimate_credits(prompt: str, completion: str = "", minimum: int = 1) -> int:
    tokens = estimate_tokens(prompt) + estimate_tokens(completion)
    return max(minimum, math.ceil(tokens / 250))


def get_or_create_wallet(db: Session, owner_type: str, user_id: Optional[int], school_id: Optional[int]) -> models.AIWallet:
    wallet = db.query(models.AIWallet).filter(
        models.AIWallet.owner_type == owner_type,
        models.AIWallet.user_id == user_id,
        models.AIWallet.school_id == school_id,
    ).first()
    if wallet:
        return wallet
    wallet = models.AIWallet(owner_type=owner_type, user_id=user_id, school_id=school_id, status="active")
    db.add(wallet)
    db.flush()
    return wallet


def wallet_for_user(db: Session, user: models.User) -> models.AIWallet:
    return get_or_create_wallet(db, "user", user.id, user.school_id)


def wallet_for_school(db: Session, school_id: int) -> models.AIWallet:
    return get_or_create_wallet(db, "school", None, school_id)


def wallet_for_purchase(db: Session, owner_type: str, user: models.User, target_user_id: Optional[int] = None) -> models.AIWallet:
    if owner_type == "school":
        if not user.school_id:
            raise HTTPException(status_code=400, detail="School context is required")
        return wallet_for_school(db, user.school_id)
    if owner_type == "user" and target_user_id and target_user_id != user.id:
        target = db.query(models.User).filter(models.User.id == target_user_id).first()
        if not target or (user.school_id and target.school_id != user.school_id):
            raise HTTPException(status_code=404, detail="Target user not found")
        return get_or_create_wallet(db, "user", target.id, target.school_id)
    return wallet_for_user(db, user)


def ensure_credits(db: Session, user: models.User, required_credits: int) -> models.AIWallet:
    wallet = wallet_for_user(db, user)
    if user.role == models.UserRole.SUPER_ADMIN:
        wallet.status = "active"
        wallet.daily_credit_limit = None
        wallet.monthly_credit_limit = None
        if wallet.balance_credits < required_credits:
            wallet.balance_credits = required_credits
        db.add(wallet)
        db.flush()
        return wallet
    if wallet.status != "active" or wallet.balance_credits < required_credits:
        usage = models.AIUsageLog(
            user_id=user.id,
            school_id=user.school_id,
            wallet_id=wallet.id,
            module_name="ai_agent",
            action_type="blocked_insufficient_credits",
            credits_charged=0,
            status="blocked",
            error_message=INSUFFICIENT_AI_CREDITS,
        )
        db.add(usage)
        db.flush()
        raise HTTPException(status_code=402, detail=INSUFFICIENT_AI_CREDITS)
    now = datetime.utcnow()
    if wallet.daily_credit_limit is not None:
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        used_today = int(db.query(func.coalesce(func.sum(models.AIUsageLog.credits_charged), 0)).filter(
            models.AIUsageLog.user_id == user.id,
            models.AIUsageLog.created_at >= day_start,
            models.AIUsageLog.status == "successful",
        ).scalar() or 0)
        if used_today + required_credits > wallet.daily_credit_limit:
            _record_credit_block(db, user, wallet, required_credits, "blocked_daily_limit")
            raise HTTPException(status_code=429, detail=AI_CREDIT_LIMIT_REACHED)
    if user.school_id:
        school_wallet = wallet_for_school(db, user.school_id)
        if school_wallet.monthly_credit_limit is not None:
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            used_month = int(db.query(func.coalesce(func.sum(models.AIUsageLog.credits_charged), 0)).filter(
                models.AIUsageLog.school_id == user.school_id,
                models.AIUsageLog.created_at >= month_start,
                models.AIUsageLog.status == "successful",
            ).scalar() or 0)
            if used_month + required_credits > school_wallet.monthly_credit_limit:
                _record_credit_block(db, user, school_wallet, required_credits, "blocked_monthly_school_limit")
                raise HTTPException(status_code=429, detail=AI_CREDIT_LIMIT_REACHED)
    return wallet


def _record_credit_block(db: Session, user: models.User, wallet: models.AIWallet, required_credits: int, action_type: str) -> None:
    db.add(models.AIUsageLog(
        user_id=user.id,
        school_id=user.school_id,
        wallet_id=wallet.id,
        module_name="ai_agent",
        action_type=action_type,
        credits_charged=0,
        status="blocked",
        error_message=f"{AI_CREDIT_LIMIT_REACHED} Required credits: {required_credits}",
    ))
    db.flush()


def record_usage(
    db: Session,
    user: models.User,
    prompt: str,
    response_text: str,
    module_name: str,
    action_type: str,
    status: str = "successful",
    error_message: Optional[str] = None,
    provider: Optional[models.AIProvider] = None,
    model_name: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
) -> models.AIUsageLog:
    provider = provider or active_provider(db)
    prompt_tokens = prompt_tokens if prompt_tokens is not None else estimate_tokens(prompt)
    completion_tokens = completion_tokens if completion_tokens is not None else estimate_tokens(response_text)
    credits = max(1, math.ceil((prompt_tokens + completion_tokens) / 250))
    wallet = ensure_credits(db, user, credits) if status == "successful" else wallet_for_user(db, user)
    before = wallet.balance_credits
    if status == "successful":
        wallet.balance_credits -= credits
        wallet.total_used_credits += credits
        _consume_school_allocations(db, user, credits)
    input_cost = (provider.cost_per_1k_input_tokens if provider else 0) * prompt_tokens / 1000
    output_cost = (provider.cost_per_1k_output_tokens if provider else 0) * completion_tokens / 1000
    usage = models.AIUsageLog(
        user_id=user.id,
        school_id=user.school_id,
        wallet_id=wallet.id,
        provider_id=provider.id if provider else None,
        model_name=model_name or (provider.default_model if provider else None),
        module_name=module_name,
        action_type=action_type,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        credits_charged=credits if status == "successful" else 0,
        estimated_cost=input_cost + output_cost,
        currency=(provider.currency if provider else "USD"),
        request_summary=(prompt or "")[:500],
        status=status,
        error_message=error_message,
    )
    db.add(usage)
    db.flush()
    if status == "successful":
        transaction = models.AICreditTransaction(
            wallet_id=wallet.id,
            user_id=user.id,
            school_id=user.school_id,
            transaction_type="usage",
            credits_amount=-credits,
            balance_before=before,
            balance_after=wallet.balance_credits,
            usage_log_id=usage.id,
            description=f"AI usage: {module_name}/{action_type}",
        )
        db.add(transaction)
    return usage


def apply_platform_payment_success(db: Session, payment: models.PlatformPayment, actor: Optional[models.User] = None) -> None:
    if payment.status != "successful" or payment.wallet_id is None or payment.credits_amount <= 0:
        return
    existing = db.query(models.AICreditTransaction).filter(
        models.AICreditTransaction.payment_id == payment.id,
        models.AICreditTransaction.transaction_type == "purchase",
    ).first()
    if existing:
        return
    wallet = db.query(models.AIWallet).filter(models.AIWallet.id == payment.wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="AI wallet not found")
    before = wallet.balance_credits
    wallet.balance_credits += payment.credits_amount
    wallet.total_purchased_credits += payment.credits_amount
    transaction = models.AICreditTransaction(
        wallet_id=wallet.id,
        user_id=wallet.user_id,
        school_id=wallet.school_id,
        transaction_type="purchase",
        credits_amount=payment.credits_amount,
        balance_before=before,
        balance_after=wallet.balance_credits,
        payment_id=payment.id,
        description=f"Achat credits IA {payment.reference}",
    )
    db.add(transaction)
    if actor:
        audit.record_audit(
            db,
            action="ai_credits.purchase_applied",
            current_user=actor,
            entity_type="platform_payment",
            entity_id=payment.reference,
            details={"credits": payment.credits_amount, "wallet_id": wallet.id},
        )


def grant_school_credits(
    db: Session,
    school_id: int,
    user_id: int,
    credits_amount: int,
    actor: models.User,
    note: Optional[str] = None,
) -> models.SchoolAICreditAllocation:
    if credits_amount <= 0:
        raise HTTPException(status_code=400, detail="Le nombre de crédits doit être positif")
    target = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.school_id == school_id,
        models.User.is_active == True,  # noqa: E712
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable dans cet établissement")
    school_wallet = db.query(models.AIWallet).filter(
        models.AIWallet.owner_type == "school",
        models.AIWallet.school_id == school_id,
    ).with_for_update().first() or wallet_for_school(db, school_id)
    if school_wallet.balance_credits < credits_amount:
        raise HTTPException(status_code=400, detail="Le solde de crédits IA de l'établissement est insuffisant")
    user_wallet = wallet_for_user(db, target)
    school_before = school_wallet.balance_credits
    user_before = user_wallet.balance_credits
    school_wallet.balance_credits -= credits_amount
    user_wallet.balance_credits += credits_amount
    user_wallet.total_purchased_credits += credits_amount
    allocation = models.SchoolAICreditAllocation(
        school_id=school_id,
        user_id=user_id,
        school_wallet_id=school_wallet.id,
        user_wallet_id=user_wallet.id,
        allocated_credits=credits_amount,
        remaining_credits=credits_amount,
        consumed_credits=0,
        is_active=True,
        granted_by_id=actor.id,
        updated_by_id=actor.id,
        note=note,
    )
    db.add(allocation)
    db.flush()
    db.add_all([
        models.AICreditTransaction(
            wallet_id=school_wallet.id,
            school_id=school_id,
            transaction_type="school_distribution",
            credits_amount=-credits_amount,
            balance_before=school_before,
            balance_after=school_wallet.balance_credits,
            description=f"Crédits distribués à l'utilisateur #{user_id}",
        ),
        models.AICreditTransaction(
            wallet_id=user_wallet.id,
            user_id=user_id,
            school_id=school_id,
            transaction_type="school_allocation",
            credits_amount=credits_amount,
            balance_before=user_before,
            balance_after=user_wallet.balance_credits,
            description=note or f"Allocation de l'établissement #{school_id}",
        ),
    ])
    return allocation


def revoke_school_allocation(
    db: Session,
    allocation: models.SchoolAICreditAllocation,
    actor: models.User,
) -> models.SchoolAICreditAllocation:
    if not allocation.is_active:
        return allocation
    refundable = allocation.remaining_credits
    school_wallet = db.query(models.AIWallet).filter(models.AIWallet.id == allocation.school_wallet_id).with_for_update().first()
    user_wallet = db.query(models.AIWallet).filter(models.AIWallet.id == allocation.user_wallet_id).with_for_update().first()
    if not school_wallet or not user_wallet:
        raise HTTPException(status_code=404, detail="Portefeuille IA introuvable")
    if refundable > user_wallet.balance_credits:
        raise HTTPException(status_code=409, detail="Le portefeuille utilisateur ne permet pas de restituer les crédits non consommés")
    school_before = school_wallet.balance_credits
    user_before = user_wallet.balance_credits
    user_wallet.balance_credits -= refundable
    school_wallet.balance_credits += refundable
    allocation.remaining_credits = 0
    allocation.is_active = False
    allocation.updated_by_id = actor.id
    if refundable:
        db.add_all([
            models.AICreditTransaction(
                wallet_id=user_wallet.id,
                user_id=allocation.user_id,
                school_id=allocation.school_id,
                transaction_type="school_allocation_revoked",
                credits_amount=-refundable,
                balance_before=user_before,
                balance_after=user_wallet.balance_credits,
                description=f"Restitution de l'allocation #{allocation.id}",
            ),
            models.AICreditTransaction(
                wallet_id=school_wallet.id,
                school_id=allocation.school_id,
                transaction_type="school_allocation_refund",
                credits_amount=refundable,
                balance_before=school_before,
                balance_after=school_wallet.balance_credits,
                description=f"Crédits non consommés restitués depuis l'allocation #{allocation.id}",
            ),
        ])
    return allocation


def _consume_school_allocations(db: Session, user: models.User, credits: int) -> None:
    remaining = credits
    allocations = db.query(models.SchoolAICreditAllocation).filter(
        models.SchoolAICreditAllocation.user_id == user.id,
        models.SchoolAICreditAllocation.school_id == user.school_id,
        models.SchoolAICreditAllocation.is_active == True,  # noqa: E712
        models.SchoolAICreditAllocation.remaining_credits > 0,
    ).order_by(models.SchoolAICreditAllocation.created_at.asc()).all()
    for allocation in allocations:
        consumed = min(remaining, allocation.remaining_credits)
        allocation.remaining_credits -= consumed
        allocation.consumed_credits += consumed
        if allocation.remaining_credits == 0:
            allocation.is_active = False
        remaining -= consumed
        if remaining == 0:
            break


def usage_summary(db: Session, school_id: Optional[int] = None) -> dict:
    usage = db.query(models.AIUsageLog)
    payments = db.query(models.PlatformPayment)
    wallets = db.query(models.AIWallet)
    if school_id:
        usage = usage.filter(models.AIUsageLog.school_id == school_id)
        payments = payments.filter(models.PlatformPayment.school_id == school_id)
        wallets = wallets.filter(models.AIWallet.school_id == school_id)
    return {
        "credits_used": int(usage.with_entities(func.coalesce(func.sum(models.AIUsageLog.credits_charged), 0)).scalar() or 0),
        "tokens_used": int(usage.with_entities(func.coalesce(func.sum(models.AIUsageLog.total_tokens), 0)).scalar() or 0),
        "estimated_cost": float(usage.with_entities(func.coalesce(func.sum(models.AIUsageLog.estimated_cost), 0)).scalar() or 0),
        "credits_sold": int(payments.filter(models.PlatformPayment.status == "successful").with_entities(func.coalesce(func.sum(models.PlatformPayment.credits_amount), 0)).scalar() or 0),
        "wallet_balance": int(wallets.with_entities(func.coalesce(func.sum(models.AIWallet.balance_credits), 0)).scalar() or 0),
    }
