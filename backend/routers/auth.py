from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import localization, models, schemas, security, database

router = APIRouter(prefix="/auth", tags=["Authentication"])




@router.post("/register/school", response_model=schemas.SchoolResponse)
def register_school(school: schemas.SchoolCreate, owner: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
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
    except Exception as e:
        db.rollback()
        import traceback
        print("FULL TRACEBACK:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active or (user.school and not user.school.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account or school is suspended")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user
