import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .migrations import ensure_runtime_schema
from .routers import auth, students, teachers, chat, education, attendance, grades, dashboard, library, finance, system, pedagogy, operations, enterprise

# Create Tables (Simple migration for MVP)
Base.metadata.create_all(bind=engine)
ensure_runtime_schema(engine)

app = FastAPI(title="Education SaaS API")

# Configure CORS
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def read_root():
    return {"message": "Welcome to Education SaaS API"}
