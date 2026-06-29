import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from .audit import audit_mutation_middleware
from .database import SessionLocal
from .observability import observability_middleware
from .security_middleware import rate_limit_middleware, security_headers_middleware
from . import models
from .routers import auth, students, teachers, chat, education, attendance, grades, dashboard, library, finance, system, pedagogy, operations, enterprise, documents, files, internships, ai_automation, ai_billing, bootstrap, account, context, student_lifecycle, employment, site, facilities, transport, payments, platform, sis, academics, communication, hr, analytics, extensibility

app = FastAPI(title="TeducAI API")
START_TIME = time.time()

# Configure CORS
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
if os.getenv("APP_ENV") == "production" and "*" in cors_origins:
    raise RuntimeError("CORS_ALLOWED_ORIGINS cannot contain '*' in production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(security_headers_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(audit_mutation_middleware)
app.middleware("http")(observability_middleware)

app.include_router(auth.router)
# app.include_router(tenants.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(chat.router)
app.include_router(education.router)
app.include_router(grades.router)
app.include_router(attendance.router)
app.include_router(dashboard.router)
app.include_router(library.router)
app.include_router(finance.router)
app.include_router(system.router)
app.include_router(pedagogy.router)
app.include_router(operations.router)
app.include_router(transport.router)
app.include_router(payments.router)
app.include_router(platform.router)
app.include_router(sis.router)
app.include_router(academics.router)
app.include_router(communication.router)
app.include_router(hr.router)
app.include_router(analytics.router)
app.include_router(extensibility.router)
app.include_router(enterprise.router)
app.include_router(documents.router)
app.include_router(files.router)
app.include_router(internships.router)
app.include_router(ai_automation.router)
app.include_router(ai_billing.router)
app.include_router(bootstrap.router)
app.include_router(account.router)
app.include_router(context.router)
app.include_router(student_lifecycle.router)
app.include_router(employment.router)
app.include_router(site.router)
app.include_router(facilities.router)


@app.on_event("startup")
def bootstrap_env_ai_providers() -> None:
    """Register AI providers from .env.production keys so they drive chat/sync.

    Best-effort: never block app startup if the table or DB is not ready."""
    from .services import ai_provider_bootstrap
    db = SessionLocal()
    try:
        ai_provider_bootstrap.bootstrap_providers_from_env(db)
    except Exception:  # pragma: no cover - startup must not crash on bootstrap
        db.rollback()
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to TeducAI API"}


@app.get("/health")
def health_check():
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "environment": os.getenv("APP_ENV", "development"),
    }


@app.get("/ready")
def readiness_check():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        migration_version = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        return {"ready": True, "database": "ok", "migration_version": migration_version}
    except Exception as exc:
        return {"ready": False, "database": "error", "detail": str(exc)[:200]}
    finally:
        db.close()


@app.get("/metrics")
def metrics():
    db = SessionLocal()
    try:
        counts = {
            "schools": db.query(func.count(models.School.id)).scalar() or 0,
            "users": db.query(func.count(models.User.id)).scalar() or 0,
            "students": db.query(func.count(models.StudentProfile.id)).scalar() or 0,
            "audit_logs": db.query(func.count(models.AuditLog.id)).scalar() or 0,
            "security_events": db.query(func.count(models.SecurityEvent.id)).scalar() or 0,
            "secure_files": db.query(func.count(models.SecureFile.id)).scalar() or 0,
        }
    except Exception:
        counts = {}
    finally:
        db.close()
    uptime = int(time.time() - START_TIME)
    lines = [
        "# HELP education_saas_uptime_seconds API process uptime.",
        "# TYPE education_saas_uptime_seconds gauge",
        f"education_saas_uptime_seconds {uptime}",
    ]
    for key, value in counts.items():
        lines.append(f"education_saas_{key}_total {value}")
    return "\n".join(lines) + "\n"
