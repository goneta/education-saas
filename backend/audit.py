from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.requests import Request

from . import database, models, security


MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIPPED_PATHS = {"/auth/token"}
SENSITIVE_DETAIL_KEYS = {
    "authorization",
    "api_key",
    "api_key_secret",
    "access_token",
    "refresh_token",
    "token",
    "secret",
    "password",
    "hashed_password",
    "mfa_secret",
    "otp",
    "otp_code",
}


def sanitize_audit_details(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(sensitive in key_text for sensitive in SENSITIVE_DETAIL_KEYS):
                sanitized[key] = "***"
            else:
                sanitized[key] = sanitize_audit_details(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_audit_details(item) for item in value]
    return value


def record_audit(
    db: Session,
    *,
    action: str,
    current_user: models.User | None = None,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    details: dict | None = None,
) -> None:
    row = models.AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=sanitize_audit_details(details) if details else None,
        actor_id=current_user.id if current_user else None,
        school_id=current_user.school_id if current_user else None,
    )
    db.add(row)


def _user_from_request(db: Session, request: Request) -> models.User | None:
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    except JWTError:
        return None
    email = payload.get("sub")
    if not email:
        return None
    return db.query(models.User).filter(models.User.email == email).first()


async def audit_mutation_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.method not in MUTATION_METHODS or request.url.path in SKIPPED_PATHS:
        return response
    db = database.SessionLocal()
    try:
        user = _user_from_request(db, request)
        db.add(models.AuditLog(
            action=f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            actor_id=user.id if user else None,
            school_id=user.school_id if user else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    return response
