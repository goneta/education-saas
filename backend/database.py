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

def is_production() -> bool:
    """Single source of truth for "this process serves production".

    A host that ships `.env.production` IS a production host even when the
    process manager did not export APP_ENV — the same rule the SECRET_KEY guard
    has always used, now shared by every production check (DB, webhooks).
    """
    return os.getenv("APP_ENV") == "production" or ENV_PRODUCTION_FILE.exists()


def validate_database_url(url: str, *, production: bool, configured: bool) -> None:
    """Refuse to serve production on the SQLite development fallback.

    Audit CFG-01: `DATABASE_URL` defaulted to a local SQLite file, so a missing
    variable let the app start *normally* on a file nobody backs up — data loss
    discovered days later. Production must fail loudly at boot instead, exactly
    like the SECRET_KEY guard. Pure function so the rule is unit-testable.
    """
    if not production:
        return
    if not configured:
        raise RuntimeError(
            "DATABASE_URL must be configured in production (refusing to start on the "
            "SQLite development fallback). Set DATABASE_URL to the PostgreSQL instance."
        )
    if url.startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL points at SQLite while APP_ENV=production (or .env.production "
            "exists). Production requires PostgreSQL — refusing to start."
        )


_DATABASE_URL_ENV = os.getenv("DATABASE_URL")
SQLALCHEMY_DATABASE_URL = _DATABASE_URL_ENV or "sqlite:///./education_saas.db"
validate_database_url(
    SQLALCHEMY_DATABASE_URL, production=is_production(), configured=bool(_DATABASE_URL_ENV)
)

def _engine_options(url: str) -> dict:
    """Connection settings (audit PERF-03).

    `pool_pre_ping` is not optional in production: after a PostgreSQL restart or
    an idle-timeout cut, the pool otherwise hands out dead connections and every
    request 500s until the application is restarted. `pool_recycle` renews
    connections before a proxy or the server drops them; the pool is sized
    explicitly instead of relying on the default of 5.
    """
    if "sqlite" in url:
        return {"connect_args": {"check_same_thread": False}}
    return {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    }


engine = create_engine(SQLALCHEMY_DATABASE_URL, **_engine_options(SQLALCHEMY_DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
