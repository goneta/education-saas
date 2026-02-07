from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Enum as SqEnum, DateTime, Text, JSON, Time, Float, UniqueConstraint
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

class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

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
    subjects = relationship("Subject", back_populates="school")

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
    timetables = relationship("Timetable", back_populates="teacher")

    # Profile details
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

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
    grades = relationship("Grade", back_populates="student")
    education_history = relationship("StudentEducationHistory", back_populates="student", cascade="all, delete-orphan")

class StudentEducationHistory(Base):
    __tablename__ = "student_education_history"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    
    previous_school = Column(String, nullable=False)
    class_level = Column(String, nullable=False) # e.g. "Terminale", "Bachelor 1"
    degree_obtained = Column(String, nullable=True) # e.g. "Baccalaureat"
    grade_average = Column(String, nullable=True) # e.g. "14/20" or "B+"
    year_completed = Column(Integer, nullable=True)
    
    student = relationship("StudentProfile", back_populates="education_history")

class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    specialization = Column(String, nullable=True)
    join_date = Column(DateTime, nullable=True)
    bio = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="teacher_profile")

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
    assessments = relationship("Assessment", back_populates="term")

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
    timetables = relationship("Timetable", back_populates="class_")
    assessments = relationship("Assessment", back_populates="current_class")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, index=True) # e.g. MATH101
    description = Column(String, nullable=True)
    coefficient = Column(Integer, default=1)
    
    school_id = Column(Integer, ForeignKey("schools.id"))
    school = relationship("School", back_populates="subjects")
    
    timetables = relationship("Timetable", back_populates="subject")
    assessments = relationship("Assessment", back_populates="subject")

class Timetable(Base):
    __tablename__ = "timetables"

    id = Column(Integer, primary_key=True, index=True)
    
    day_of_week = Column(SqEnum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room = Column(String, nullable=True)
    
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    class_ = relationship("Class", back_populates="timetables")
    
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    subject = relationship("Subject", back_populates="timetables")
    
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    teacher = relationship("User", back_populates="timetables")

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

# Grade & Assessment Models

class AssessmentType(str, enum.Enum):
    EXAM = "exam"
    HOMEWORK = "homework"
    QUIZ = "quiz"
    PROJECT = "project"
    PARTICIPATION = "participation"

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(SqEnum(AssessmentType), default=AssessmentType.EXAM)
    date = Column(DateTime, nullable=False)
    max_score = Column(Integer, default=20)
    weight = Column(Integer, default=1) # Coefficient within calculation
    
    # Relationships
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    current_class = relationship("Class", back_populates="assessments")
    
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    subject = relationship("Subject", back_populates="assessments")
    
    term_id = Column(Integer, ForeignKey("terms.id"), nullable=False)
    term = relationship("Term", back_populates="assessments")
    
    grades = relationship("Grade", back_populates="assessment", cascade="all, delete-orphan")

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float, nullable=False) 
    comment = Column(String, nullable=True)
    
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    assessment = relationship("Assessment", back_populates="grades")
    
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    student = relationship("StudentProfile", back_populates="grades")

    # Avoid duplicates
    __table_args__ = (
        UniqueConstraint('assessment_id', 'student_id', name='_assessment_student_uc'),
    ) 


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True) # The specific date of the class
    status = Column(SqEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT)
    remarks = Column(String, nullable=True)
    
    # Links
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    student = relationship("StudentProfile")
    
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=False)
    timetable = relationship("Timetable")
    

    
    # Metadata
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Teacher or Admin who marked it
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Library Management Models

class BookStatus(str, enum.Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    LOST = "lost"
    DAMAGED = "damaged"

class LoanStatus(str, enum.Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    isbn = Column(String, unique=True, index=True, nullable=True)
    category = Column(String, index=True, nullable=True)
    
    quantity = Column(Integer, default=1)
    available_quantity = Column(Integer, default=1)
    location = Column(String, nullable=True) # e.g. "Shelf A1"
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    school = relationship("School")
    
    loans = relationship("Loan", back_populates="book")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Borrower (Student or Teacher)
    
    issue_date = Column(DateTime, default=func.now())
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    
    status = Column(SqEnum(LoanStatus), default=LoanStatus.ACTIVE)
    notes = Column(String, nullable=True)
    
    book = relationship("Book", back_populates="loans")
    user = relationship("User") # We can add back_populates="loans" to User if needed, but not strictly required yet


