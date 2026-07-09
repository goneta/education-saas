"""Enterprise Billing & Subscription — unified `/billing` API.

One surface over the platform's existing money infrastructure: the Subscription
tab drives `/system/subscription/*`; credit purchases and wallet management drive
`/ai_billing`; this router adds the *aggregation* (overview), the billing
*configuration* (preferences, tax, auto-recharge), promo codes, and projected
invoice/transaction/audit/revenue views.

RBAC: billing management is limited to admin / direction / accounting. Read-only
billing users get the read endpoints. Revenue analytics and promo-code authoring
are Super-Admin only. Every mutation is audit-logged (see services/billing.py).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import database, models, schemas, security
from ..services import ai_credits, billing
from ..services import email_service

router = APIRouter(prefix="/billing", tags=["Billing"])

_MANAGE_ROLES = (
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTOR,
    models.UserRole.ACCOUNTANT,
)
_READ_ROLES = _MANAGE_ROLES  # read-only billing users can be added here later


def _ensure_manage(current_user: models.User) -> None:
    if current_user.role not in _MANAGE_ROLES:
        raise HTTPException(status_code=403, detail="Accès facturation réservé à l'administration / comptabilité.")


def _ensure_super_admin(current_user: models.User) -> None:
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Réservé au Super Admin.")


def _school_id(current_user: models.User, school_id: Optional[int]) -> int:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if not school_id:
            raise HTTPException(status_code=400, detail="school_id requis pour le Super Admin.")
        return school_id
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Contexte d'établissement requis.")
    return current_user.school_id


def _school_wallet(db: Session, school_id: int) -> models.AIWallet:
    return ai_credits.get_or_create_wallet(db, "school", None, school_id)


# --- Overview & catalog ------------------------------------------------------

@router.get("/overview")
def get_overview(school_id: Optional[int] = None, db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    data = billing.overview(db, resolved)
    db.commit()
    return data


@router.get("/plans")
def get_plans(current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    return {"plans": billing.PLAN_CATALOG}


# --- Preferences -------------------------------------------------------------

@router.get("/preferences", response_model=schemas.BillingPreferenceResponse)
def get_preferences(school_id: Optional[int] = None, db: Session = Depends(database.get_db),
                    current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    pref = billing.get_preferences(db, resolved)
    db.commit()
    return pref


@router.put("/preferences", response_model=schemas.BillingPreferenceResponse)
def put_preferences(payload: schemas.BillingPreferenceUpdate, school_id: Optional[int] = None,
                    db: Session = Depends(database.get_db),
                    current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    pref = billing.update_preferences(db, resolved, payload.model_dump(exclude_unset=True), current_user)
    db.commit()
    db.refresh(pref)
    return pref


# --- Tax profile -------------------------------------------------------------

@router.get("/tax", response_model=schemas.BillingTaxResponse)
def get_tax(school_id: Optional[int] = None, db: Session = Depends(database.get_db),
            current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    tax = billing.get_tax(db, resolved)
    db.commit()
    return tax


@router.put("/tax", response_model=schemas.BillingTaxResponse)
def put_tax(payload: schemas.BillingTaxUpdate, school_id: Optional[int] = None,
            db: Session = Depends(database.get_db),
            current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    tax = billing.update_tax(db, resolved, payload.model_dump(exclude_unset=True), current_user)
    db.commit()
    db.refresh(tax)
    return tax


# --- Auto-recharge -----------------------------------------------------------

@router.get("/auto-recharge", response_model=schemas.AutoRechargeResponse)
def get_auto_recharge(school_id: Optional[int] = None, db: Session = Depends(database.get_db),
                      current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    cfg = billing.get_auto_recharge(db, _school_wallet(db, resolved))
    db.commit()
    return cfg


@router.put("/auto-recharge", response_model=schemas.AutoRechargeResponse)
def put_auto_recharge(payload: schemas.AutoRechargeUpdate, school_id: Optional[int] = None,
                      db: Session = Depends(database.get_db),
                      current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    cfg = billing.update_auto_recharge(db, _school_wallet(db, resolved),
                                       payload.model_dump(exclude_unset=True), current_user)
    db.commit()
    db.refresh(cfg)
    return cfg


# --- Promo codes -------------------------------------------------------------

@router.post("/promos/validate")
def validate_promo(payload: schemas.PromoValidateRequest, school_id: Optional[int] = None,
                   db: Session = Depends(database.get_db),
                   current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    return billing.validate_promo(db, payload.code, school_id=resolved,
                                  context=payload.context, base_amount=payload.base_amount)


@router.post("/promos/redeem")
def redeem_promo(payload: schemas.PromoValidateRequest, school_id: Optional[int] = None,
                 db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    result = billing.redeem_promo(db, payload.code, school_id=resolved, user=current_user,
                                  context=payload.context, base_amount=payload.base_amount)
    if not result.get("valid"):
        db.rollback()
        raise HTTPException(status_code=400, detail=result.get("reason", "invalid_code"))
    db.commit()
    return result


# --- Invoices / transactions / usage / audit --------------------------------

@router.get("/invoices")
def get_invoices(school_id: Optional[int] = None, status: Optional[str] = None, limit: int = 100,
                 db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    return {"invoices": billing.list_invoices(db, resolved, status=status, limit=limit)}


@router.get("/invoices/{payment_id}")
def get_invoice_detail(payment_id: int, school_id: Optional[int] = None,
                       db: Session = Depends(database.get_db),
                       current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    detail = billing.invoice_detail(db, resolved, payment_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    return detail


@router.post("/invoices/{payment_id}/email")
def email_invoice(payment_id: int, payload: schemas.InvoiceEmailRequest, school_id: Optional[int] = None,
                  db: Session = Depends(database.get_db),
                  current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    if not email_service.is_configured():
        raise HTTPException(status_code=503, detail="Service e-mail non configuré (SMTP).")
    try:
        result = billing.email_invoice(db, resolved, payment_id, current_user, recipients=payload.recipients)
    except ValueError:
        raise HTTPException(status_code=400, detail="Aucun destinataire. Ajoutez une adresse ou un destinataire de facturation.")
    except email_service.EmailNotConfigured:
        raise HTTPException(status_code=503, detail="Service e-mail non configuré (SMTP).")
    except email_service.EmailSendError as exc:
        raise HTTPException(status_code=502, detail=f"Échec d'envoi de l'e-mail: {exc}")
    if not result:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    db.commit()
    return result


@router.get("/invoices/{payment_id}/pdf")
def get_invoice_pdf(payment_id: int, school_id: Optional[int] = None,
                    db: Session = Depends(database.get_db),
                    current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    detail = billing.invoice_detail(db, resolved, payment_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    pdf = billing.render_invoice_pdf(detail)
    filename = f"invoice-{detail.get('number', payment_id)}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/transactions")
def get_transactions(school_id: Optional[int] = None, status: Optional[str] = None,
                     payment_type: Optional[str] = None, limit: int = 200,
                     db: Session = Depends(database.get_db),
                     current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    return {"transactions": billing.list_transactions(db, resolved, status=status,
                                                      payment_type=payment_type, limit=limit)}


@router.get("/usage")
def get_usage(school_id: Optional[int] = None, db: Session = Depends(database.get_db),
              current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    wallet = _school_wallet(db, resolved)
    summary = ai_credits.usage_summary(db, school_id=resolved)
    db.commit()
    return {"summary": summary, "balance_credits": wallet.balance_credits}


@router.get("/usage/timeseries")
def get_usage_timeseries(days: int = 30, school_id: Optional[int] = None,
                         db: Session = Depends(database.get_db),
                         current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    return billing.usage_timeseries(db, resolved, days=days)


@router.get("/audit", response_model=List[schemas.BillingAuditResponse])
def get_audit(school_id: Optional[int] = None, limit: int = 100,
              db: Session = Depends(database.get_db),
              current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    # Super Admin may view all-school billing audit by omitting school_id.
    resolved = school_id if current_user.role == models.UserRole.SUPER_ADMIN else _school_id(current_user, school_id)
    return billing.list_audit(db, school_id=resolved, limit=limit)


# --- Saved payment methods ---------------------------------------------------

@router.get("/payment-methods")
def list_payment_methods(school_id: Optional[int] = None, db: Session = Depends(database.get_db),
                         current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    return {"methods": billing.list_payment_methods(db, resolved)}


@router.post("/payment-methods")
def add_payment_method(payload: schemas.PaymentMethodCreate, school_id: Optional[int] = None,
                       db: Session = Depends(database.get_db),
                       current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    method = billing.add_payment_method(db, resolved, payload.model_dump(exclude_unset=True), current_user)
    db.commit()
    return billing.serialize_method(method)


@router.patch("/payment-methods/{method_id}")
def update_payment_method(method_id: int, payload: schemas.PaymentMethodUpdate, school_id: Optional[int] = None,
                          db: Session = Depends(database.get_db),
                          current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    method = billing.update_payment_method(db, resolved, method_id, payload.model_dump(exclude_unset=True), current_user)
    if not method:
        raise HTTPException(status_code=404, detail="Moyen de paiement introuvable.")
    db.commit()
    return billing.serialize_method(method)


@router.post("/payment-methods/{method_id}/default")
def set_default_payment_method(method_id: int, school_id: Optional[int] = None,
                               db: Session = Depends(database.get_db),
                               current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    method = billing.set_default_payment_method(db, resolved, method_id, current_user)
    if not method:
        raise HTTPException(status_code=404, detail="Moyen de paiement introuvable.")
    db.commit()
    return billing.serialize_method(method)


@router.delete("/payment-methods/{method_id}")
def remove_payment_method(method_id: int, school_id: Optional[int] = None,
                          db: Session = Depends(database.get_db),
                          current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    if not billing.remove_payment_method(db, resolved, method_id, current_user):
        raise HTTPException(status_code=404, detail="Moyen de paiement introuvable.")
    db.commit()
    return {"removed": True}


# --- AI billing assistant ----------------------------------------------------

@router.post("/assistant")
def ask_assistant(payload: schemas.BillingAssistantRequest, school_id: Optional[int] = None,
                  db: Session = Depends(database.get_db),
                  current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    result = billing.billing_assistant(db, resolved, current_user, payload.question,
                                       language=payload.language or "fr")
    db.commit()
    return result


# --- Super-admin -------------------------------------------------------------

@router.get("/admin/revenue")
def get_revenue(db: Session = Depends(database.get_db),
                current_user: models.User = Depends(security.get_current_user)):
    _ensure_super_admin(current_user)
    return billing.revenue_summary(db)


@router.get("/admin/promos", response_model=List[schemas.PromoCodeResponse])
def list_promos(db: Session = Depends(database.get_db),
                current_user: models.User = Depends(security.get_current_user)):
    _ensure_super_admin(current_user)
    return db.query(models.BillingPromoCode).order_by(models.BillingPromoCode.created_at.desc()).all()


@router.post("/admin/promos", response_model=schemas.PromoCodeResponse)
def create_promo(payload: schemas.PromoCodeCreate, db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(security.get_current_user)):
    _ensure_super_admin(current_user)
    code = payload.code.strip()
    if db.query(models.BillingPromoCode).filter(models.BillingPromoCode.code == code).first():
        raise HTTPException(status_code=409, detail="Code déjà existant.")
    promo = models.BillingPromoCode(**{**payload.model_dump(), "code": code, "created_by_id": current_user.id})
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo
