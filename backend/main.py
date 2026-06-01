import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .audit import audit_mutation_middleware
from .database import SessionLocal
from .security_middleware import rate_limit_middleware, security_headers_middleware
from .routers import auth, students, teachers, chat, education, attendance, grades, dashboard, library, finance, system, pedagogy, operations, enterprise, documents

app = FastAPI(title="Education SaaS API")

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
app.include_router(enterprise.router)
app.include_router(documents.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Education SaaS API"}


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
