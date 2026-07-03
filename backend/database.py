from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
if os.getenv("APP_ENV") == "production":
    load_dotenv(".env.production", override=True)
elif os.getenv("APP_ENV") is None and not os.path.exists(".env") and os.path.exists(".env.production"):
    # Production hosts often ship only .env.production (no .env, and APP_ENV not
    # exported by the process manager). Honor it as the env source so provider
    # keys, DATABASE_URL, etc. load without requiring APP_ENV to be set first.
    load_dotenv(".env.production")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./education_saas.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
