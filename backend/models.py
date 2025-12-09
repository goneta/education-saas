from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Enum as SqEnum, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

# Enums
class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin" # Ministry / Platform Owner
    SCHOOL_ADMIN = "school_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    STAFF = "staff"

class SchoolType(str, enum.Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    VOCATIONAL = "vocational"

# Core Models

class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    domain_prefix = Column(String, unique=True, index=True, nullable=False) # subdomain
    school_type = Column(SqEnum(SchoolType), default=SchoolType.GENERAL)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    website = Column(String)
    logo_url = Column(String)
    
    subscription_plan = Column(String, default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="school", cascade="all, delete-orphan")
    academic_years = relationship("AcademicYear", back_populates="school")
    classes = relationship("Class", back_populates="school")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    role = Column(SqEnum(UserRole), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Tenancy
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True) # Null for Super Admin
    school = relationship("School", back_populates="users")

    # Profile details
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Academic Info
    registration_number = Column(String, unique=True, index=True) # Matricule
    date_of_birth = Column(DateTime)
    gender = Column(String) # M/F
    student_address = Column(String, nullable=True) # Added field
    
    # Parent/Guardian Info
    parent_name = Column(String)
    parent_phone = Column(String)
    parent_email = Column(String, nullable=True)
    parent_address = Column(String, nullable=True) # Added field
    
    # Class Linkage
    current_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    
    user = relationship("User", back_populates="student_profile")
    current_class = relationship("Class", back_populates="students")

class AcademicYear(Base):
    __tablename__ = "academic_years"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g. "2024-2025"
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_current = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"))
    school = relationship("School", back_populates="academic_years")
    
    terms = relationship("Term", back_populates="academic_year")

class Term(Base):
    __tablename__ = "terms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g. "Trimester 1"
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"))
    academic_year = relationship("AcademicYear", back_populates="terms")

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g. "6eme A", "Grade 10"
    level = Column(String) # e.g. "6eme", "10"
    
    school_id = Column(Integer, ForeignKey("schools.id"))
    school = relationship("School", back_populates="classes")
    
    # Simplify: One main teacher per class
    main_teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    main_teacher = relationship("User", foreign_keys=[main_teacher_id])

    students = relationship("StudentProfile", back_populates="current_class")

class ReferenceData(Base):
    __tablename__ = "reference_data"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True, nullable=False) # e.g. "EDUCATION_LEVEL", "SUBJECT_CATEGORY"
    key = Column(String, index=True, nullable=False) # e.g. "PRIM_CP"
    value = Column(JSON, nullable=False) # e.g. {"fr": "CP", "en": "Grade 1"}
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Scope: Null = Global System Default, Set = School Specific
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
