from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Enum as SqEnum, DateTime, Text, JSON, Time, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

# Enums
class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin" # Ministry / Platform Owner
    SCHOOL_ADMIN = "school_admin"
    CASHIER = "cashier"
    REGISTRAR = "registrar"
    DIRECTION = "direction"
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

class StudentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"

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
    guardian_relation = Column(String, nullable=True)
    status = Column(SqEnum(StudentStatus), default=StudentStatus.UNASSIGNED, nullable=False)
    previous_level = Column(String, nullable=True)
    previous_class = Column(String, nullable=True)
    
    # Class Linkage
    current_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    
    user = relationship("User", back_populates="student_profile")
    current_class = relationship("Class", back_populates="students")
    grades = relationship("Grade", back_populates="student")
    education_history = relationship("StudentEducationHistory", back_populates="student", cascade="all, delete-orphan")
    registration_documents = relationship("StudentRegistrationDocument", back_populates="student", cascade="all, delete-orphan")

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

class FeeStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"

class CertificateType(str, enum.Enum):
    SCHOOLING = "schooling"
    ENROLLMENT = "enrollment"
    ABSENCE_AUTHORIZATION = "absence_authorization"
    PAYMENT = "payment"

class CertificateStatus(str, enum.Enum):
    GENERATED = "generated"
    BLOCKED = "blocked"

class CashClosureStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"

class ExpenseCategory(str, enum.Enum):
    SALARIES = "salaries"
    UTILITIES = "utilities"
    MAINTENANCE = "maintenance"
    SUPPLIES = "supplies"
    EQUIPMENT = "equipment"
    OTHER = "other"

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


# Finance Management Models

class Fee(Base):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(SqEnum(FeeStatus), default=FeeStatus.PENDING, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    category_order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    covered_by = Column(JSON, nullable=True)

    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)

    student = relationship("StudentProfile")
    school = relationship("School")
    academic_year = relationship("AcademicYear")
    class_ = relationship("Class")
    payments = relationship("Payment", back_populates="fee", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def total_paid(self):
        return sum(payment.amount for payment in self.payments)

    @property
    def remaining_balance(self):
        return max(self.amount - self.total_paid, 0)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    note = Column(String, nullable=True)
    receipt_number = Column(String, unique=True, index=True, nullable=True)
    operator_station = Column(String, nullable=True)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fee_id = Column(Integer, ForeignKey("fees.id"), nullable=False)
    fee = relationship("Fee", back_populates="payments")
    recorded_by = relationship("User")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(SqEnum(ExpenseCategory), default=ExpenseCategory.OTHER, nullable=False)
    date = Column(DateTime, nullable=True)
    description = Column(String, nullable=True)

    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    school = relationship("School")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FeeSchedule(Base):
    __tablename__ = "fee_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category_order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    is_current = Column(Boolean, default=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    level = Column(String, nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    school = relationship("School")
    academic_year = relationship("AcademicYear")
    class_ = relationship("Class")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StudentRegistrationDocument(Base):
    __tablename__ = "student_registration_documents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    is_received = Column(Boolean, default=False)
    received_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("StudentProfile", back_populates="registration_documents")
    updated_by = relationship("User")


class CertificateRequest(Base):
    __tablename__ = "certificate_requests"

    id = Column(Integer, primary_key=True, index=True)
    certificate_type = Column(SqEnum(CertificateType), nullable=False)
    status = Column(SqEnum(CertificateStatus), default=CertificateStatus.GENERATED, nullable=False)
    blocked_reason = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    generated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("StudentProfile")
    school = relationship("School")
    generated_by = relationship("User")


class CashClosure(Base):
    __tablename__ = "cash_closures"

    id = Column(Integer, primary_key=True, index=True)
    closure_date = Column(DateTime, nullable=False, index=True)
    counted_amount = Column(Float, nullable=False)
    expected_amount = Column(Float, nullable=False)
    difference = Column(Float, nullable=False)
    status = Column(SqEnum(CashClosureStatus), default=CashClosureStatus.SUBMITTED, nullable=False)
    notes = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)

    school = relationship("School")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class BudgetForecast(Base):
    __tablename__ = "budget_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    expected_students = Column(Integer, default=0)
    expected_revenue = Column(Float, default=0)
    fee_category = Column(String, nullable=True, index=True)
    level = Column(String, nullable=True, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school = relationship("School")
    academic_year = relationship("AcademicYear")
    class_ = relationship("Class")
    created_by = relationship("User")


class SmsMessage(Base):
    __tablename__ = "sms_messages"

    id = Column(Integer, primary_key=True, index=True)
    recipient_phone = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)
    event_type = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="queued", nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("StudentProfile")
    school = relationship("School")
    created_by = relationship("User")



