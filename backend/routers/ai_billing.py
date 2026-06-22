import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .. import audit, crypto_utils, database, models, rbac, schemas, security
from ..services import ai_credits, payment_gateway


router = APIRouter(tags=["AI Credits & Payments"])


def _super_admin(user: models.User) -> None:
    if user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin only")


def _school_context(user: models.User) -> int:
    if not user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return user.school_id


def _provider_response(row: models.AIProvider) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "provider_type": row.provider_type,
        "base_url": row.base_url,
        "default_model": row.default_model,
        "is_active": row.is_active,
        "priority": row.priority,
        "cost_per_1k_input_tokens": row.cost_per_1k_input_tokens,
        "cost_per_1k_output_tokens": row.cost_per_1k_output_tokens,
        "currency": row.currency,
        "has_api_key": bool(row.api_key_encrypted),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _payment_account_response(row: models.SchoolPaymentAccount) -> dict:
    return {
        "id": row.id,
        "school_id": row.school_id,
        "provider": row.provider,
        "account_name": row.account_name,
        "merchant_id": row.merchant_id,
        "phone_number": row.phone_number,
        "country_code": row.country_code,
        "is_active": row.is_active,
        "has_api_key": bool(row.api_key_encrypted),
        "has_secret_key": bool(row.secret_key_encrypted),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _platform_payment_response(
    row: models.PlatformPayment,
    *,
    checkout_url: Optional[str] = None,
    provider_status: Optional[str] = None,
) -> dict:
    return {
        "id": row.id,
        "reference": row.reference,
        "payer_user_id": row.payer_user_id,
        "school_id": row.school_id,
        "payment_type": row.payment_type,
        "amount": row.amount,
        "currency": row.currency,
        "country_code": row.country_code,
        "region": row.region,
        "provider": row.provider,
        "provider_reference": row.provider_reference,
        "status": row.status,
        "beneficiary_entity": row.beneficiary_entity,
        "pack_id": row.pack_id,
        "credits_amount": row.credits_amount,
        "wallet_id": row.wallet_id,
        "validated_by_id": row.validated_by_id,
        "validated_at": row.validated_at,
        "metadata_json": row.metadata_json,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "checkout_url": checkout_url,
        "provider_status": provider_status,
    }


def _verify_webhook(secret_env: str, provided: Optional[str]) -> None:
    secret = os.getenv(secret_env)
    if secret and provided != secret:
        raise HTTPException(status_code=403, detail="Invalid webhook signature")


def _allocation_response(row: models.SchoolAICreditAllocation) -> dict:
    return {
        "id": row.id,
        "school_id": row.school_id,
        "user_id": row.user_id,
        "school_wallet_id": row.school_wallet_id,
        "user_wallet_id": row.user_wallet_id,
        "allocated_credits": row.allocated_credits,
        "remaining_credits": row.remaining_credits,
        "consumed_credits": row.consumed_credits,
        "is_active": row.is_active,
        "granted_by_id": row.granted_by_id,
        "updated_by_id": row.updated_by_id,
        "note": row.note,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


@router.get("/platform/ai/providers", response_model=list[schemas.AIProviderResponse])
def list_ai_providers(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    return [_provider_response(row) for row in db.query(models.AIProvider).order_by(models.AIProvider.priority.asc()).all()]


@router.post("/platform/ai/providers", response_model=schemas.AIProviderResponse)
def create_ai_provider(payload: schemas.AIProviderCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    row = models.AIProvider(
        name=payload.name,
        provider_type=payload.provider_type,
        api_key_encrypted=crypto_utils.encrypt_secret(payload.api_key),
        base_url=payload.base_url,
        default_model=payload.default_model,
        is_active=payload.is_active,
        priority=payload.priority,
        cost_per_1k_input_tokens=payload.cost_per_1k_input_tokens,
        cost_per_1k_output_tokens=payload.cost_per_1k_output_tokens,
        currency=payload.currency,
    )
    db.add(row)
    db.flush()
    audit.record_audit(db, action="platform.ai_provider.created", current_user=current_user, entity_type="ai_provider", entity_id=row.id, details={"provider_type": row.provider_type})
    db.commit()
    db.refresh(row)
    return _provider_response(row)


@router.put("/platform/ai/providers/{provider_id}", response_model=schemas.AIProviderResponse)
def update_ai_provider(provider_id: int, payload: schemas.AIProviderUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    row = db.query(models.AIProvider).filter(models.AIProvider.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider not found")
    updates = payload.model_dump(exclude_unset=True)
    api_key = updates.pop("api_key", None)
    for key, value in updates.items():
        setattr(row, key, value)
    if api_key is not None:
        row.api_key_encrypted = crypto_utils.encrypt_secret(api_key)
    audit.record_audit(db, action="platform.ai_provider.updated", current_user=current_user, entity_type="ai_provider", entity_id=row.id, details={"fields": sorted(updates.keys())})
    db.commit()
    db.refresh(row)
    return _provider_response(row)


@router.delete("/platform/ai/providers/{provider_id}")
def delete_ai_provider(provider_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    row = db.query(models.AIProvider).filter(models.AIProvider.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider not found")
    row.is_active = False
    audit.record_audit(db, action="platform.ai_provider.disabled", current_user=current_user, entity_type="ai_provider", entity_id=row.id)
    db.commit()
    return {"status": "disabled"}


@router.get("/platform/ai/credit-packs", response_model=list[schemas.AICreditPackResponse])
def list_ai_credit_packs(country_code: Optional[str] = None, active_only: bool = False, db: Session = Depends(database.get_db)):
    query = db.query(models.AICreditPack)
    if country_code:
        query = query.filter(models.AICreditPack.country_code == country_code)
    if active_only:
        query = query.filter(models.AICreditPack.is_active == True)  # noqa: E712
    return query.order_by(models.AICreditPack.price.asc()).all()


@router.post("/platform/ai/credit-packs", response_model=schemas.AICreditPackResponse)
def create_ai_credit_pack(payload: schemas.AICreditPackCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    row = models.AICreditPack(**payload.model_dump())
    db.add(row)
    db.flush()
    audit.record_audit(db, action="platform.ai_credit_pack.created", current_user=current_user, entity_type="ai_credit_pack", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.put("/platform/ai/credit-packs/{pack_id}", response_model=schemas.AICreditPackResponse)
def update_ai_credit_pack(pack_id: int, payload: schemas.AICreditPackUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    row = db.query(models.AICreditPack).filter(models.AICreditPack.id == pack_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Pack not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)
    audit.record_audit(db, action="platform.ai_credit_pack.updated", current_user=current_user, entity_type="ai_credit_pack", entity_id=row.id, details={"fields": sorted(updates.keys())})
    db.commit()
    db.refresh(row)
    return row


@router.delete("/platform/ai/credit-packs/{pack_id}")
def delete_ai_credit_pack(pack_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    row = db.query(models.AICreditPack).filter(models.AICreditPack.id == pack_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Pack not found")
    row.is_active = False
    audit.record_audit(db, action="platform.ai_credit_pack.disabled", current_user=current_user, entity_type="ai_credit_pack", entity_id=row.id)
    db.commit()
    return {"status": "disabled"}


@router.get("/platform/ai/usage", response_model=list[schemas.AIUsageLogResponse])
def platform_ai_usage(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    return db.query(models.AIUsageLog).order_by(models.AIUsageLog.created_at.desc()).limit(500).all()


@router.get("/platform/ai/payments", response_model=list[schemas.PlatformPaymentResponse])
def platform_ai_payments(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    return db.query(models.PlatformPayment).order_by(models.PlatformPayment.created_at.desc()).limit(500).all()


@router.get("/platform/ai/credit-targets")
def platform_ai_credit_targets(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    users = db.query(models.User).filter(models.User.is_active == True).order_by(models.User.role, models.User.full_name).all()  # noqa: E712
    schools = db.query(models.School).filter(models.School.is_active == True).order_by(models.School.name).all()  # noqa: E712
    return {
        "users": [
            {"id": row.id, "full_name": row.full_name, "email": row.email, "role": row.role.value, "school_id": row.school_id}
            for row in users
        ],
        "schools": [{"id": row.id, "name": row.name, "country_code": row.country_code} for row in schools],
    }


@router.post("/platform/ai/manual-payments", response_model=schemas.PlatformPaymentResponse)
def create_manual_ai_credit_payment(
    payload: schemas.ManualAICreditPaymentRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _super_admin(current_user)
    pack = db.query(models.AICreditPack).filter(models.AICreditPack.id == payload.pack_id, models.AICreditPack.is_active == True).first()  # noqa: E712
    if not pack:
        raise HTTPException(status_code=404, detail="Pack de crédits IA introuvable")
    if pack.target_type not in {"both", payload.owner_type}:
        raise HTTPException(status_code=400, detail="Ce pack ne peut pas être attribué à ce type de bénéficiaire")
    if payload.payment_method == "free" and not (payload.note or "").strip():
        raise HTTPException(status_code=400, detail="Un motif est obligatoire pour une attribution gratuite")
    target_user = None
    target_school = None
    if payload.owner_type == "user":
        if not payload.user_id:
            raise HTTPException(status_code=400, detail="L'utilisateur bénéficiaire est obligatoire")
        target_user = db.query(models.User).filter(models.User.id == payload.user_id, models.User.is_active == True).first()  # noqa: E712
        if not target_user:
            raise HTTPException(status_code=404, detail="Utilisateur bénéficiaire introuvable")
        wallet = ai_credits.get_or_create_wallet(db, "user", target_user.id, target_user.school_id)
        target_school_id = target_user.school_id
    else:
        if not payload.school_id:
            raise HTTPException(status_code=400, detail="L'établissement bénéficiaire est obligatoire")
        target_school = db.query(models.School).filter(models.School.id == payload.school_id, models.School.is_active == True).first()  # noqa: E712
        if not target_school:
            raise HTTPException(status_code=404, detail="Établissement bénéficiaire introuvable")
        wallet = ai_credits.wallet_for_school(db, target_school.id)
        target_school_id = target_school.id
    payment = models.PlatformPayment(
        reference=ai_credits.platform_payment_reference("CASH" if payload.payment_method == "cash" else "FREE"),
        payer_user_id=current_user.id,
        school_id=target_school_id,
        payment_type="ai_credit_purchase" if payload.payment_method == "cash" else "ai_credit_grant",
        amount=pack.price if payload.payment_method == "cash" else 0,
        currency=pack.currency,
        country_code=pack.country_code,
        region=pack.region,
        provider=payload.payment_method,
        provider_reference=payload.internal_reference,
        status="successful",
        beneficiary_entity=ai_credits.beneficiary_for_region(pack.country_code, pack.region),
        pack_id=pack.id,
        credits_amount=pack.credits_amount,
        wallet_id=wallet.id,
        validated_by_id=current_user.id,
        validated_at=datetime.utcnow(),
        metadata_json={
            "manual_validation": True,
            "note": payload.note,
            "owner_type": payload.owner_type,
            "target_user_id": target_user.id if target_user else None,
            "target_school_id": target_school.id if target_school else target_school_id,
        },
    )
    db.add(payment)
    db.flush()
    ai_credits.apply_platform_payment_success(db, payment, current_user)
    audit.record_audit(
        db,
        action=f"platform.ai_credit_payment.{payload.payment_method}_validated",
        current_user=current_user,
        entity_type="platform_payment",
        entity_id=payment.reference,
        details={
            "owner_type": payload.owner_type,
            "target_user_id": target_user.id if target_user else None,
            "target_school_id": target_school_id,
            "pack_id": pack.id,
            "credits": pack.credits_amount,
        },
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/platform/ai/wallets/adjust", response_model=schemas.AICreditTransactionResponse)
def adjust_ai_wallet(payload: schemas.AICreditAdjustmentRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    if payload.owner_type == "user":
        if not payload.user_id:
            raise HTTPException(status_code=400, detail="user_id is required for user wallet adjustments")
        target_user = db.query(models.User).filter(models.User.id == payload.user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        wallet = ai_credits.get_or_create_wallet(db, "user", target_user.id, target_user.school_id)
        school_id = target_user.school_id
        user_id = target_user.id
    else:
        if not payload.school_id:
            raise HTTPException(status_code=400, detail="school_id is required for school wallet adjustments")
        school = db.query(models.School).filter(models.School.id == payload.school_id).first()
        if not school:
            raise HTTPException(status_code=404, detail="School not found")
        wallet = ai_credits.wallet_for_school(db, school.id)
        school_id = school.id
        user_id = None
    before = wallet.balance_credits
    wallet.balance_credits += payload.credits_amount
    if payload.credits_amount > 0:
        wallet.total_purchased_credits += payload.credits_amount
    transaction = models.AICreditTransaction(
        wallet_id=wallet.id,
        user_id=user_id,
        school_id=school_id,
        transaction_type=payload.transaction_type,
        credits_amount=payload.credits_amount,
        balance_before=before,
        balance_after=wallet.balance_credits,
        description=payload.description or "Super Admin AI credit adjustment",
    )
    db.add(transaction)
    db.flush()
    audit.record_audit(db, action="platform.ai_wallet.adjusted", current_user=current_user, entity_type="ai_wallet", entity_id=wallet.id, details={"credits": payload.credits_amount, "owner_type": payload.owner_type})
    db.commit()
    db.refresh(transaction)
    return transaction


@router.put("/platform/ai/wallets/{wallet_id}/limits", response_model=schemas.AIWalletResponse)
def update_ai_wallet_limits(wallet_id: int, payload: schemas.AIWalletLimitUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    wallet = db.query(models.AIWallet).filter(models.AIWallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="AI wallet not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(wallet, key, value)
    audit.record_audit(db, action="platform.ai_wallet.limits_updated", current_user=current_user, entity_type="ai_wallet", entity_id=wallet.id, details=updates)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/platform/ai/analytics")
def platform_ai_analytics(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _super_admin(current_user)
    return ai_credits.usage_summary(db)


@router.get("/school/ai/wallet", response_model=schemas.AIWalletResponse)
def school_ai_wallet(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_reports:view", db)
    wallet = ai_credits.wallet_for_school(db, school_id)
    db.commit()
    return wallet


@router.get("/school/ai/usage", response_model=list[schemas.AIUsageLogResponse])
def school_ai_usage(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_reports:view", db)
    return db.query(models.AIUsageLog).filter(models.AIUsageLog.school_id == school_id).order_by(models.AIUsageLog.created_at.desc()).limit(300).all()


@router.get("/school/ai/users")
def school_ai_users(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_credits:view", db)
    users = db.query(models.User).filter(
        models.User.school_id == school_id,
        models.User.is_active == True,  # noqa: E712
    ).order_by(models.User.role, models.User.full_name).all()
    result = []
    for row in users:
        wallet = ai_credits.wallet_for_user(db, row)
        result.append({
            "id": row.id,
            "full_name": row.full_name,
            "email": row.email,
            "role": row.role.value,
            "ai_wallet_status": wallet.status,
            "ai_credit_balance": wallet.balance_credits,
        })
    db.commit()
    return result


@router.put("/school/ai/users/{user_id}/access", response_model=schemas.AIWalletResponse)
def update_school_user_ai_access(
    user_id: int,
    payload: schemas.AIWalletAccessUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_credits:edit", db)
    target = db.query(models.User).filter(models.User.id == user_id, models.User.school_id == school_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable dans cet établissement")
    wallet = ai_credits.wallet_for_user(db, target)
    wallet.status = "active" if payload.is_active else "suspended"
    audit.record_audit(
        db,
        action="school.ai_credits.access_updated",
        current_user=current_user,
        entity_type="ai_wallet",
        entity_id=wallet.id,
        details={"user_id": user_id, "status": wallet.status},
    )
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/school/ai/allocations", response_model=list[schemas.SchoolAICreditAllocationResponse])
def school_ai_allocations(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_credits:view", db)
    rows = db.query(models.SchoolAICreditAllocation).filter(
        models.SchoolAICreditAllocation.school_id == school_id,
    ).order_by(models.SchoolAICreditAllocation.created_at.desc()).limit(500).all()
    return [_allocation_response(row) for row in rows]


@router.post("/school/ai/allocations", response_model=schemas.SchoolAICreditAllocationResponse)
def create_school_ai_allocation(
    payload: schemas.SchoolAICreditAllocationCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_credits:create", db)
    allocation = ai_credits.grant_school_credits(db, school_id, payload.user_id, payload.credits_amount, current_user, payload.note)
    audit.record_audit(
        db,
        action="school.ai_credits.allocated",
        current_user=current_user,
        entity_type="school_ai_credit_allocation",
        entity_id=allocation.id,
        details={"user_id": payload.user_id, "credits": payload.credits_amount},
    )
    db.commit()
    db.refresh(allocation)
    return _allocation_response(allocation)


@router.delete("/school/ai/allocations/{allocation_id}", response_model=schemas.SchoolAICreditAllocationResponse)
def revoke_school_ai_allocation(
    allocation_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_credits:edit", db)
    allocation = db.query(models.SchoolAICreditAllocation).filter(
        models.SchoolAICreditAllocation.id == allocation_id,
        models.SchoolAICreditAllocation.school_id == school_id,
    ).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation introuvable")
    refunded = allocation.remaining_credits
    ai_credits.revoke_school_allocation(db, allocation, current_user)
    audit.record_audit(
        db,
        action="school.ai_credits.revoked",
        current_user=current_user,
        entity_type="school_ai_credit_allocation",
        entity_id=allocation.id,
        details={"user_id": allocation.user_id, "refunded_credits": refunded},
    )
    db.commit()
    db.refresh(allocation)
    return _allocation_response(allocation)


@router.post("/school/ai/purchase", response_model=schemas.PlatformPaymentResponse)
def school_ai_purchase(payload: schemas.AICreditPurchaseRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _school_context(current_user)
    rbac.require_permission(current_user, "ai_credits:create", db)
    payload.owner_type = "school"
    return initiate_platform_payment(schemas.PlatformPaymentCreate(
        pack_id=payload.pack_id,
        provider=payload.provider,
        payment_type="ai_credit_purchase",
        owner_type="school",
        mobile_money_network=payload.mobile_money_network,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        metadata_json={"note": payload.note} if payload.note else None,
    ), current_user, db)


@router.get("/school/ai/transactions", response_model=list[schemas.AICreditTransactionResponse])
def school_ai_transactions(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "ai_reports:view", db)
    return db.query(models.AICreditTransaction).filter(models.AICreditTransaction.school_id == school_id).order_by(models.AICreditTransaction.created_at.desc()).limit(300).all()


@router.get("/me/ai/wallet", response_model=schemas.AIWalletResponse)
def my_ai_wallet(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    wallet = ai_credits.wallet_for_user(db, current_user)
    db.commit()
    return wallet


@router.get("/me/ai/usage", response_model=list[schemas.AIUsageLogResponse])
def my_ai_usage(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    return db.query(models.AIUsageLog).filter(models.AIUsageLog.user_id == current_user.id).order_by(models.AIUsageLog.created_at.desc()).limit(200).all()


@router.post("/me/ai/purchase", response_model=schemas.PlatformPaymentResponse)
def my_ai_purchase(payload: schemas.AICreditPurchaseRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    payload.owner_type = "user"
    return initiate_platform_payment(schemas.PlatformPaymentCreate(
        pack_id=payload.pack_id,
        provider=payload.provider,
        payment_type="ai_credit_purchase",
        owner_type="user",
        mobile_money_network=payload.mobile_money_network,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        metadata_json={"note": payload.note} if payload.note else None,
    ), current_user, db)


@router.get("/me/ai/transactions", response_model=list[schemas.AICreditTransactionResponse])
def my_ai_transactions(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    wallet = ai_credits.wallet_for_user(db, current_user)
    return db.query(models.AICreditTransaction).filter(models.AICreditTransaction.wallet_id == wallet.id).order_by(models.AICreditTransaction.created_at.desc()).limit(200).all()


@router.post("/platform/payments/initiate", response_model=schemas.PlatformPaymentResponse)
def initiate_platform_payment(payload: schemas.PlatformPaymentCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    pack = db.query(models.AICreditPack).filter(models.AICreditPack.id == payload.pack_id).first() if payload.pack_id else None
    if payload.payment_type == "ai_credit_purchase" and not pack:
        raise HTTPException(status_code=404, detail="AI credit pack not found")
    if pack and pack.target_type not in {"both", payload.owner_type}:
        raise HTTPException(status_code=400, detail="This AI credit pack is not available for the selected beneficiary")
    if payload.provider not in {"cash", "free", "stripe", "djamo", "cinetpay"}:
        raise HTTPException(status_code=400, detail="Unsupported AI credit payment method")
    note = str((payload.metadata_json or {}).get("note") or "").strip()
    if payload.provider == "free" and not note:
        raise HTTPException(status_code=400, detail="Un motif est obligatoire pour une demande gratuite")
    amount = 0 if payload.provider == "free" else payload.amount if payload.amount is not None else (pack.price if pack else 0)
    currency = payload.currency or (pack.currency if pack else "FCFA")
    country_code = payload.country_code or (pack.country_code if pack else (current_user.school.country_code if current_user.school else "CI"))
    region = payload.region or (pack.region if pack else None)
    wallet = ai_credits.wallet_for_purchase(db, payload.owner_type, current_user, payload.target_user_id)
    payment = models.PlatformPayment(
        reference=ai_credits.platform_payment_reference("TPL"),
        payer_user_id=current_user.id,
        school_id=current_user.school_id,
        payment_type=payload.payment_type,
        amount=amount,
        currency=currency,
        country_code=country_code,
        region=region,
        provider=payload.provider,
        provider_reference=payload.provider_reference,
        status="pending_manual_validation" if payload.provider in {"cash", "free"} else "pending",
        beneficiary_entity=payload.beneficiary_entity or ai_credits.beneficiary_for_region(country_code, region),
        pack_id=pack.id if pack else payload.pack_id,
        credits_amount=payload.credits_amount or (pack.credits_amount if pack else 0),
        wallet_id=wallet.id,
        metadata_json={**(payload.metadata_json or {}), "separation": "platform_payment_to_teducai", "owner_type": payload.owner_type},
    )
    db.add(payment)
    db.flush()
    checkout_url = None
    provider_status = payment.status
    if payload.provider in {"stripe", "djamo", "cinetpay"}:
        session = payment_gateway.create_checkout_session(
            provider=payload.provider,
            reference=payment.reference,
            amount=payment.amount,
            currency=payment.currency,
            title=pack.name if pack else "Crédits IA TeducAI",
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
            mobile_money_network=payload.mobile_money_network,
        )
        payment.provider_reference = session.provider_reference
        payment.status = session.status
        payment.metadata_json = {
            **(payment.metadata_json or {}),
            "provider_payload": session.provider_payload,
            "mobile_money_network": payload.mobile_money_network,
        }
        checkout_url = session.checkout_url
        provider_status = session.status
    audit.record_audit(db, action="platform.payment.initiated", current_user=current_user, entity_type="platform_payment", entity_id=payment.reference, details={"beneficiary": payment.beneficiary_entity, "amount": amount, "currency": currency})
    db.commit()
    db.refresh(payment)
    return _platform_payment_response(payment, checkout_url=checkout_url, provider_status=provider_status)


@router.post("/platform/payments/webhook", response_model=schemas.PlatformPaymentResponse)
def platform_payment_webhook(payload: schemas.PlatformPaymentWebhook, x_teducai_webhook_secret: Optional[str] = Header(default=None), db: Session = Depends(database.get_db)):
    _verify_webhook("PLATFORM_PAYMENT_WEBHOOK_SECRET", x_teducai_webhook_secret)
    payment = db.query(models.PlatformPayment).filter(models.PlatformPayment.reference == payload.reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Platform payment not found")
    payment.status = payload.status
    payment.provider_reference = payload.provider_reference or payment.provider_reference
    payment.metadata_json = {**(payment.metadata_json or {}), **(payload.metadata_json or {})}
    if payload.status == "successful":
        ai_credits.apply_platform_payment_success(db, payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/platform/payments/{payment_id}", response_model=schemas.PlatformPaymentResponse)
def get_platform_payment(payment_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    payment = db.query(models.PlatformPayment).filter(models.PlatformPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if current_user.role != models.UserRole.SUPER_ADMIN and payment.payer_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return payment


@router.post("/platform/ai/payments/{payment_id}/manual-validate", response_model=schemas.PlatformPaymentResponse)
def validate_manual_ai_payment(
    payment_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _super_admin(current_user)
    payment = db.query(models.PlatformPayment).filter(models.PlatformPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement plateforme introuvable")
    if payment.provider not in {"cash", "free"}:
        raise HTTPException(status_code=400, detail="Ce paiement n'est pas une demande manuelle")
    if payment.status == "successful":
        return payment
    if payment.status != "pending_manual_validation":
        raise HTTPException(status_code=409, detail="Ce paiement ne peut plus être validé")
    payment.status = "successful"
    payment.validated_by_id = current_user.id
    payment.validated_at = datetime.utcnow()
    ai_credits.apply_platform_payment_success(db, payment, current_user)
    audit.record_audit(
        db,
        action="platform.ai_credit_payment.manual_validated",
        current_user=current_user,
        entity_type="platform_payment",
        entity_id=payment.reference,
        details={"provider": payment.provider, "credits": payment.credits_amount, "wallet_id": payment.wallet_id},
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/school/payment-accounts", response_model=list[schemas.SchoolPaymentAccountResponse])
def list_school_payment_accounts(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "settings:view", db)
    return [_payment_account_response(row) for row in db.query(models.SchoolPaymentAccount).filter(models.SchoolPaymentAccount.school_id == school_id).all()]


@router.post("/school/payment-accounts", response_model=schemas.SchoolPaymentAccountResponse)
def create_school_payment_account(payload: schemas.SchoolPaymentAccountCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "settings:write", db)
    row = models.SchoolPaymentAccount(
        school_id=school_id,
        provider=payload.provider,
        account_name=payload.account_name,
        merchant_id=payload.merchant_id,
        api_key_encrypted=crypto_utils.encrypt_secret(payload.api_key),
        secret_key_encrypted=crypto_utils.encrypt_secret(payload.secret_key),
        phone_number=payload.phone_number,
        country_code=payload.country_code,
        is_active=payload.is_active,
    )
    db.add(row)
    db.flush()
    audit.record_audit(db, action="school.payment_account.created", current_user=current_user, entity_type="school_payment_account", entity_id=row.id, details={"provider": row.provider})
    db.commit()
    db.refresh(row)
    return _payment_account_response(row)


@router.get("/school/payments", response_model=list[schemas.SchoolPaymentResponse])
def list_school_payments(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "payments:view", db)
    return db.query(models.SchoolPayment).filter(models.SchoolPayment.school_id == school_id).order_by(models.SchoolPayment.created_at.desc()).limit(500).all()


@router.post("/school/payments/initiate", response_model=schemas.SchoolPaymentResponse)
def initiate_school_payment(payload: schemas.SchoolPaymentCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    school_id = _school_context(current_user)
    rbac.require_permission(current_user, "payments:create", db)
    if payload.school_beneficiary_account_id:
        account = db.query(models.SchoolPaymentAccount).filter(
            models.SchoolPaymentAccount.id == payload.school_beneficiary_account_id,
            models.SchoolPaymentAccount.school_id == school_id,
        ).first()
        if not account:
            raise HTTPException(status_code=404, detail="School payment account not found")
    row = models.SchoolPayment(
        reference=ai_credits.platform_payment_reference("SCH"),
        school_id=school_id,
        payer_user_id=current_user.id,
        student_id=payload.student_id,
        invoice_id=payload.invoice_id,
        payment_type=payload.payment_type,
        amount=payload.amount,
        currency=payload.currency,
        provider=payload.provider,
        provider_reference=payload.provider_reference,
        school_beneficiary_account_id=payload.school_beneficiary_account_id,
        status="pending",
        metadata_json={**(payload.metadata_json or {}), "separation": "school_payment_to_school_account"},
    )
    db.add(row)
    db.flush()
    audit.record_audit(db, action="school.payment.initiated", current_user=current_user, entity_type="school_payment", entity_id=row.reference, details={"amount": row.amount, "currency": row.currency, "beneficiary": "school"})
    db.commit()
    db.refresh(row)
    return row


@router.post("/school/payments/webhook", response_model=schemas.SchoolPaymentResponse)
def school_payment_webhook(payload: schemas.SchoolPaymentWebhook, x_teducai_webhook_secret: Optional[str] = Header(default=None), db: Session = Depends(database.get_db)):
    _verify_webhook("SCHOOL_PAYMENT_WEBHOOK_SECRET", x_teducai_webhook_secret)
    payment = db.query(models.SchoolPayment).filter(models.SchoolPayment.reference == payload.reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="School payment not found")
    payment.status = payload.status
    payment.provider_reference = payload.provider_reference or payment.provider_reference
    payment.metadata_json = {**(payment.metadata_json or {}), **(payload.metadata_json or {})}
    db.commit()
    db.refresh(payment)
    return payment
