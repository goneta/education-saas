import os

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .. import database
from ..services.super_admin import ensure_super_admin


router = APIRouter(prefix="/bootstrap", tags=["Bootstrap"])


def _require_bootstrap_token(token: str | None) -> None:
    expected = os.getenv("SUPER_ADMIN_BOOTSTRAP_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUPER_ADMIN_BOOTSTRAP_TOKEN is not configured",
        )
    if token != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")


@router.post("/super-admin")
def bootstrap_super_admin(
    x_teducai_bootstrap_token: str | None = Header(default=None),
    db: Session = Depends(database.get_db),
):
    _require_bootstrap_token(x_teducai_bootstrap_token)
    result = ensure_super_admin(db)
    db.commit()
    db.refresh(result.user)
    return {
        "status": "ready",
        "created": result.created,
        "username": result.user.username,
        "email": result.user.email,
        "role": result.user.role.value,
        "wallet_balance_credits": result.wallet.balance_credits,
    }
