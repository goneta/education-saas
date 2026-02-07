from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, students, teachers, chat, education, attendance, grades, dashboard, library

# Create Tables (Simple migration for MVP)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Education SaaS API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

@app.get("/")
def read_root():
    return {"message": "Welcome to Education SaaS API"}
