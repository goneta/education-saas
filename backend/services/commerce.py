from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import audit, models, schemas
from . import ai_credits


PLATFORM_ITEM_TYPES = {"ai_credits", "subscription", "premium_module"}
SCHOOL_ITEM_TYPES = {"school_fee", "registration_fee", "exam_fee", "transport_fee", "canteen_fee", "document_service"}


def cart_item_response(item: models.CartItem) -> dict:
    return {
        "id": item.id,
        "item_type": item.item_type,
        "title": item.title,
        "description": item.description,
        "quantity": item.quantity,
        "unit_amount": item.unit_amount,
        "currency": item.currency,
        "provider_scope": item.provider_scope,
        "source_type": item.source_type,
        "source_id": item.source_id,
        "metadata_json": item.metadata_json,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "line_total": item.quantity * item.unit_amount,
    }


def cart_response(items: Iterable[models.CartItem]) -> dict:
    rows = list(items)
    currency = rows[0].currency if rows else "FCFA"
    subtotal = sum(row.quantity * row.unit_amount for row in rows)
    return {
        "items": [cart_item_response(row) for row in rows],
        "subtotal": subtotal,
        "total": subtotal,
        "currency": currency,
    }


def add_cart_item(db: Session, user: models.User, payload: schemas.CartItemCreate) -> models.CartItem:
    provider_scope = payload.provider_scope
    if payload.item_type in PLATFORM_ITEM_TYPES:
        provider_scope = "platform"
    elif payload.item_type in SCHOOL_ITEM_TYPES:
        provider_scope = "school"
    item = models.CartItem(
        user_id=user.id,
        school_id=user.school_id,
        item_type=payload.item_type,
        title=payload.title,
        description=payload.description,
        quantity=payload.quantity,
        unit_amount=payload.unit_amount,
        currency=payload.currency,
        provider_scope=provider_scope,
        source_type=payload.source_type,
        source_id=payload.source_id,
        metadata_json=payload.metadata_json,
    )
    db.add(item)
    db.flush()
    audit.record_audit(db, action="cart.item_added", current_user=user, entity_type="cart_item", entity_id=item.id, details={"item_type": item.item_type, "scope": item.provider_scope})
    return item


def checkout_cart(db: Session, user: models.User, payload: schemas.CheckoutRequest) -> dict:
    items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).order_by(models.CartItem.created_at.asc()).all()
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    platform_payments: list[models.PlatformPayment] = []
    school_payments: list[models.SchoolPayment] = []
    provider_metadata = {
        "checkout_provider": payload.provider,
        "mobile_money_network": payload.mobile_money_network,
        "success_url": payload.success_url,
        "cancel_url": payload.cancel_url,
    }
    for item in items:
        amount = item.quantity * item.unit_amount
        metadata = {**(item.metadata_json or {}), **provider_metadata, "cart_item_id": item.id}
        if item.provider_scope == "platform":
            wallet = ai_credits.wallet_for_user(db, user)
            payment = models.PlatformPayment(
                reference=ai_credits.platform_payment_reference("TPL"),
                payer_user_id=user.id,
                school_id=user.school_id,
                payment_type=item.item_type,
                amount=amount,
                currency=item.currency,
                country_code=user.school.country_code if user.school else None,
                region="africa" if (user.school.country_code if user.school else "CI") == "CI" else "international",
                provider=payload.provider,
                status="pending",
                beneficiary_entity=ai_credits.beneficiary_for_region(user.school.country_code if user.school else None, None),
                credits_amount=int(metadata.get("credits_amount") or 0),
                wallet_id=wallet.id,
                metadata_json=metadata,
            )
            db.add(payment)
            db.flush()
            platform_payments.append(payment)
            audit.record_audit(db, action="platform.payment.initiated_from_cart", current_user=user, entity_type="platform_payment", entity_id=payment.reference, details={"amount": amount, "provider": payload.provider})
        else:
            if not user.school_id:
                raise HTTPException(status_code=400, detail="School context is required for school payments")
            payment = models.SchoolPayment(
                reference=ai_credits.platform_payment_reference("SCH"),
                school_id=user.school_id,
                payer_user_id=user.id,
                payment_type=item.item_type,
                amount=amount,
                currency=item.currency,
                provider=payload.provider,
                status="pending",
                metadata_json=metadata,
            )
            if item.source_type == "student_invoice":
                payment.invoice_id = item.source_id
            db.add(payment)
            db.flush()
            school_payments.append(payment)
            audit.record_audit(db, action="school.payment.initiated_from_cart", current_user=user, entity_type="school_payment", entity_id=payment.reference, details={"amount": amount, "provider": payload.provider})
    for item in items:
        db.delete(item)
    return {
        "platform_payments": platform_payments,
        "school_payments": school_payments,
        "checkout_url": None,
        "status": "pending",
    }
