from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import employment
from backend.services import ai_credits


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _user(db):
    school = models.School(name="Emploi", domain_prefix="emploi-agent", school_type=models.SchoolType.GENERAL)
    user = models.User(email="recruiter-agent@test.local", hashed_password="x", full_name="R", role=models.UserRole.RECRUITER, school=school, is_active=True)
    db.add_all([school, user])
    db.commit()
    return user


def test_employment_agent_records_usage_and_charges_credits():
    db = _session()
    user = _user(db)
    payload = schemas.EmploymentAgentRequest(prompt="Analyse les profils techniques disponibles.", mode="recruiter")

    result = employment.employment_agent(payload=payload, current_user=user, db=db)
    assert result["type"] == "content"

    # Usage is recorded against the employment_agent module for this user.
    logs = db.query(models.AIUsageLog).filter(
        models.AIUsageLog.user_id == user.id,
        models.AIUsageLog.module_name == "employment_agent",
    ).all()
    assert len(logs) == 1
    assert logs[0].status == "successful"
    assert logs[0].credits_charged >= 1

    # A usage transaction was written and the wallet reflects consumption.
    wallet = ai_credits.wallet_for_user(db, user)
    assert wallet.total_used_credits >= 1
    assert db.query(models.AICreditTransaction).filter(
        models.AICreditTransaction.wallet_id == wallet.id,
        models.AICreditTransaction.transaction_type == "usage",
    ).count() == 1
