import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .. import audit, crypto_utils, database, models, rbac, schemas, security
from ..services import ai_credits


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


def _verify_webhook(secret_env: str, provided: Optional[str]) -> None:
    secret = os.getenv(secret_env)
    if secret and provided != secret:
        raise HTTPException(status_code=403, detail="Invalid webhook signature")


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


@router.post("/school/ai/purchase", response_model=schemas.PlatformPaymentResponse)
def school_ai_purchase(payload: schemas.AICreditPurchaseRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    _school_context(current_user)
    rbac.require_permission(current_user, "ai_automation:create", db)
    payload.owner_type = "school"
    return initiate_platform_payment(schemas.PlatformPaymentCreate(pack_id=payload.pack_id, provider=payload.provider, payment_type="ai_credit_purchase", owner_type="school"), current_user, db)


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
    return initiate_platform_payment(schemas.PlatformPaymentCreate(pack_id=payload.pack_id, provider=payload.provider, payment_type="ai_credit_purchase", owner_type="user"), current_user, db)


@router.get("/me/ai/transactions", response_model=list[schemas.AICreditTransactionResponse])
def my_ai_transactions(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    wallet = ai_credits.wallet_for_user(db, current_user)
    return db.query(models.AICreditTransaction).filter(models.AICreditTransaction.wallet_id == wallet.id).order_by(models.AICreditTransaction.created_at.desc()).limit(200).all()


@router.post("/platform/payments/initiate", response_model=schemas.PlatformPaymentResponse)
def initiate_platform_payment(payload: schemas.PlatformPaymentCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    pack = db.query(models.AICreditPack).filter(models.AICreditPack.id == payload.pack_id).first() if payload.pack_id else None
    if payload.payment_type == "ai_credit_purchase" and not pack:
        raise HTTPException(status_code=404, detail="AI credit pack not found")
    amount = payload.amount if payload.amount is not None else (pack.price if pack else 0)
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
        status="pending",
        beneficiary_entity=payload.beneficiary_entity or ai_credits.beneficiary_for_region(country_code, region),
        pack_id=pack.id if pack else payload.pack_id,
        credits_amount=payload.credits_amount or (pack.credits_amount if pack else 0),
        wallet_id=wallet.id,
        metadata_json=payload.metadata_json or {"separation": "platform_payment_to_teducai"},
    )
    db.add(payment)
    db.flush()
    audit.record_audit(db, action="platform.payment.initiated", current_user=current_user, entity_type="platform_payment", entity_id=payment.reference, details={"beneficiary": payment.beneficiary_entity, "amount": amount, "currency": currency})
    db.commit()
    db.refresh(payment)
    return payment


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
