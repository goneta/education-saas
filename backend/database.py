from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from pathlib import Path
from dotenv import load_dotenv

# Env files are anchored to the PROJECT ROOT (the directory containing the
# `backend` package), never the process working directory. A CWD-relative
# lookup made `uvicorn backend.main:app` behave differently from the PM2
# process (different SECRET_KEY -> 401s on valid JWTs, sqlite fallback instead
# of the production DATABASE_URL) whenever it was launched from another
# directory. Root-anchoring makes every launch mode load the same files.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_PRODUCTION_FILE = PROJECT_ROOT / ".env.production"

load_dotenv(ENV_FILE)
if os.getenv("APP_ENV") == "production":
    load_dotenv(ENV_PRODUCTION_FILE, override=True)
elif os.getenv("APP_ENV") is None and not ENV_FILE.exists() and ENV_PRODUCTION_FILE.exists():
    # Production hosts often ship only .env.production (no .env, and APP_ENV not
    # exported by the process manager). Honor it as the env source so provider
    # keys, DATABASE_URL, etc. load without requiring APP_ENV to be set first.
    load_dotenv(ENV_PRODUCTION_FILE)

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
