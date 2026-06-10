from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from .. import crypto_utils, localization, models, schemas, security, database, totp

router = APIRouter(prefix="/auth", tags=["Authentication"])




@router.post("/register/school", response_model=schemas.SchoolResponse)
def register_school(school: schemas.SchoolCreate, owner: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        security.validate_password_strength(owner.password)
        # 1. Check if school exists
        db_school = db.query(models.School).filter(models.School.domain_prefix == school.domain_prefix).first()
        if db_school:
            raise HTTPException(status_code=400, detail="School domain already taken")
        
        # 2. Create School
        country_profile = localization.country_profile(school.country_code)
        currency = school.default_currency or country_profile["currency"]
        currency_code = school.currency_code or country_profile["currency_code"]
        language = school.primary_language or country_profile["locale"]
        valid_phone, phone_e164, phone_error = localization.validate_phone(school.phone, school.phone_country_code or country_profile["country_code"])
        if not valid_phone:
            raise HTTPException(status_code=400, detail=phone_error)
        address_structured = school.address_structured.model_dump() if school.address_structured else None
        if address_structured and not address_structured.get("country"):
            address_structured["country"] = country_profile["name"]
        formatted_address = localization.format_address(address_structured) or school.address

        new_school = models.School(
            name=school.name,
            domain_prefix=school.domain_prefix,
            school_type=school.school_type,
            address=school.address,
            phone=school.phone,
            email=school.email,
            country_code=country_profile["country_code"],
            default_currency=currency,
            currency_code=currency_code,
            primary_language=language,
            timezone=school.timezone or country_profile["timezone"],
            date_format=school.date_format or country_profile["date_format"],
            time_format=school.time_format or country_profile["time_format"],
            address_structured=address_structured,
            formatted_address=formatted_address,
            phone_country_code=school.phone_country_code or country_profile["country_code"],
            phone_e164=phone_e164,
        )
        db.add(new_school)
        db.commit()
        db.refresh(new_school)
        
        # 3. Create Admin User
        hashed_password = security.get_password_hash(owner.password)
        new_user = models.User(
            username=owner.username,
            email=owner.email,
            hashed_password=hashed_password,
            full_name=owner.full_name,
            role=owner.role, # Pydantic provides the Enum, passing it directly works best
            school_id=new_school.id
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_school
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    otp_code: str | None = Form(default=None),
    db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(
        or_(models.User.email == form_data.username, models.User.username == form_data.username)
    ).first()
    now = datetime.utcnow()
    if user and user.locked_until and user.locked_until > now:
        db.add(models.SecurityEvent(
            event_type="login_blocked_locked_account",
            severity="high",
            actor_id=user.id,
            school_id=user.school_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ))
        db.commit()
        raise HTTPException(status_code=423, detail="Account temporarily locked")
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
            db.add(models.SecurityEvent(
                event_type="login_failed",
                severity="medium",
                actor_id=user.id,
                school_id=user.school_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={"attempts": user.failed_login_attempts},
            ))
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active or (user.school and not user.school.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account or school is suspended")
    if user.mfa_enabled:
        secret = crypto_utils.decrypt_secret(user.mfa_secret)
        if not otp_code or not secret or not totp.verify(secret, otp_code, valid_window=1):
            db.add(models.SecurityEvent(
                event_type="mfa_failed",
                severity="high",
                actor_id=user.id,
                school_id=user.school_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ))
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA code is required or invalid")
    
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "ver": user.token_version}, expires_delta=access_token_expires
    )
    db.add(models.SecurityEvent(
        event_type="login_success",
        severity="info",
        actor_id=user.id,
        school_id=user.school_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))
    db.commit()
    return {"access_token": access_token, "token_type": "bearer", "expires_in": security.ACCESS_TOKEN_EXPIRE_MINUTES * 60}

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user


@router.post("/mfa/setup", response_model=schemas.MfaSetupResponse)
def setup_mfa(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    secret = totp.random_base32()
    current_user.mfa_secret = crypto_utils.encrypt_secret(secret)
    current_user.mfa_enabled = False
    db.commit()
    issuer = current_user.school.name if current_user.school else "TeducAI"
    return {
        "secret": secret,
        "provisioning_uri": totp.provisioning_uri(secret, name=current_user.email, issuer_name=issuer),
    }


@router.post("/mfa/enable", response_model=schemas.MfaStatusResponse)
def enable_mfa(payload: schemas.MfaVerifyRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    secret = crypto_utils.decrypt_secret(current_user.mfa_secret)
    if not secret or not totp.verify(secret, payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    current_user.mfa_enabled = True
    current_user.token_version += 1
    db.add(models.SecurityEvent(event_type="mfa_enabled", severity="medium", actor_id=current_user.id, school_id=current_user.school_id))
    db.commit()
    return {"enabled": True}


@router.post("/mfa/disable", response_model=schemas.MfaStatusResponse)
def disable_mfa(payload: schemas.MfaVerifyRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    secret = crypto_utils.decrypt_secret(current_user.mfa_secret)
    if current_user.mfa_enabled and (not secret or not totp.verify(secret, payload.code, valid_window=1)):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.token_version += 1
    db.add(models.SecurityEvent(event_type="mfa_disabled", severity="medium", actor_id=current_user.id, school_id=current_user.school_id))
    db.commit()
    return {"enabled": False}


@router.post("/logout")
def logout(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    current_user.token_version += 1
    db.commit()
    return {"message": "Logged out"}
