from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
if os.getenv("APP_ENV") == "production":
    load_dotenv(".env.production", override=True)

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
