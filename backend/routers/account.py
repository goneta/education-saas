from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security
from ..services import commerce


router = APIRouter(prefix="/account", tags=["Account"])


def _preferences(db: Session, user: models.User) -> models.UserPreference:
    prefs = db.query(models.UserPreference).filter(models.UserPreference.user_id == user.id).first()
    if prefs:
        return prefs
    prefs = models.UserPreference(user_id=user.id)
    db.add(prefs)
    db.flush()
    return prefs


@router.get("/preferences", response_model=schemas.UserPreferenceResponse)
def get_preferences(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    return _preferences(db, current_user)


@router.put("/preferences", response_model=schemas.UserPreferenceResponse)
def update_preferences(payload: schemas.UserPreferenceUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    prefs = _preferences(db, current_user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)
    audit.record_audit(db, action="account.preferences.updated", current_user=current_user, entity_type="user_preference", entity_id=prefs.id, details=payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/notifications", response_model=list[schemas.NotificationHistoryResponse])
def list_my_notifications(unread_only: bool = False, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    query = db.query(models.NotificationHistory).filter(models.NotificationHistory.recipient_user_id == current_user.id)
    if unread_only:
        query = query.filter(models.NotificationHistory.read_at.is_(None))
    return query.order_by(models.NotificationHistory.created_at.desc()).limit(100).all()


@router.get("/notifications/unread-count")
def unread_notification_count(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    count = db.query(models.NotificationHistory).filter(
        models.NotificationHistory.recipient_user_id == current_user.id,
        models.NotificationHistory.read_at.is_(None),
    ).count()
    return {"count": count}


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    row = db.query(models.NotificationHistory).filter(
        models.NotificationHistory.id == notification_id,
        models.NotificationHistory.recipient_user_id == current_user.id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.read_at = row.read_at or models.datetime.utcnow()
    audit.record_audit(db, action="account.notification.read", current_user=current_user, entity_type="notification_history", entity_id=row.id)
    db.commit()
    return {"status": "read"}


@router.get("/cart", response_model=schemas.CartResponse)
def get_cart(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).order_by(models.CartItem.created_at.asc()).all()
    return commerce.cart_response(items)


@router.post("/cart/items", response_model=schemas.CartItemResponse)
def add_cart_item(payload: schemas.CartItemCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    item = commerce.add_cart_item(db, current_user, payload)
    db.commit()
    db.refresh(item)
    return commerce.cart_item_response(item)


@router.put("/cart/items/{item_id}", response_model=schemas.CartItemResponse)
def update_cart_item(item_id: int, payload: schemas.CartItemUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    item = db.query(models.CartItem).filter(models.CartItem.id == item_id, models.CartItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    item.quantity = payload.quantity
    audit.record_audit(db, action="cart.item_updated", current_user=current_user, entity_type="cart_item", entity_id=item.id, details={"quantity": item.quantity})
    db.commit()
    db.refresh(item)
    return commerce.cart_item_response(item)


@router.delete("/cart/items/{item_id}")
def delete_cart_item(item_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    item = db.query(models.CartItem).filter(models.CartItem.id == item_id, models.CartItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    audit.record_audit(db, action="cart.item_deleted", current_user=current_user, entity_type="cart_item", entity_id=item.id)
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@router.post("/checkout", response_model=schemas.CheckoutResponse)
def checkout(payload: schemas.CheckoutRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    result = commerce.checkout_cart(db, current_user, payload)
    audit.record_audit(db, action="checkout.created", current_user=current_user, details={"provider": payload.provider, "network": payload.mobile_money_network})
    db.commit()
    return result
