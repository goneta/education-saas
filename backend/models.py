from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Enum as SqEnum, DateTime, Text, JSON, Time, Float, UniqueConstraint, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from datetime import datetime
from .database import Base

# Enums
class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin" # Ministry / Platform Owner
    SCHOOL_ADMIN = "school_admin"
    ADMIN = "admin"
    CASHIER = "cashier"
    ACCOUNTANT = "accountant"
    REGISTRAR = "registrar"
    RECEPTIONIST = "receptionist"
    SECRETARY = "secretary"
    DIRECTION = "direction"
    DIRECTOR = "director"
    PRINCIPAL = "principal"
    DEPARTMENT_HEAD = "department_head"
    PEDAGOGY_COORDINATOR = "pedagogy_coordinator"
    EDUCATOR = "educator"
    TRAINER = "trainer"
    INSTRUCTOR = "instructor"
    TEACHER = "teacher"
    STUDENT = "student"
    PUPIL = "pupil"
    PARENT = "parent"
    STAFF = "staff"

class SchoolType(str, enum.Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    GENERAL = "general"
    TECHNICAL = "technical"
    VOCATIONAL = "vocational"
    PROFESSIONAL = "professional"
    UNIVERSITY = "university"

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

class AssignmentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"

class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    GRADED = "graded"

class AdministrativeRequestType(str, enum.Enum):
    REPORT_CARD = "report_card"
    CERTIFICATE = "certificate"
    ABSENCE_AUTHORIZATION = "absence_authorization"
    OTHER = "other"

class AdministrativeRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DONE = "done"

class AdmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ENROLLED = "enrolled"

class InventoryStatus(str, enum.Enum):
    AVAILABLE = "available"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"

class PayrollStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PAID = "paid"

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
    registration_number = Column(String, nullable=True, unique=True, index=True)
    country_code = Column(String, default="CI", nullable=False)
    default_currency = Column(String, default="FCFA", nullable=False)
    currency_code = Column(String, default="XOF", nullable=False)
    primary_language = Column(String, default="fr", nullable=False)
    timezone = Column(String, default="Africa/Abidjan", nullable=False)
    date_format = Column(String, default="dd/MM/yyyy", nullable=False)
    time_format = Column(String, default="HH:mm", nullable=False)
    address_structured = Column(JSON, nullable=True)
    formatted_address = Column(String, nullable=True)
    phone_country_code = Column(String, nullable=True)
    phone_e164 = Column(String, nullable=True)
    
    subscription_plan = Column(String, default="free")
    subscription_status = Column(String, default="active", nullable=False)
    storage_quota_mb = Column(Integer, default=1024, nullable=False)
    current_billing_period_end = Column(DateTime(timezone=True), nullable=True)
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
    numref = Column(String, unique=True, index=True, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    token_version = Column(Integer, default=0, nullable=False)
    
    # Tenancy
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True) # Null for Super Admin
    school = relationship("School", back_populates="users")
    timetables = relationship("Timetable", back_populates="teacher")

    # Profile details
    phone_number = Column(String, nullable=True)
    phone_country_code = Column(String, nullable=True)
    phone_e164 = Column(String, nullable=True)
    address = Column(String, nullable=True)
    address_structured = Column(JSON, nullable=True)
    formatted_address = Column(String, nullable=True)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


@event.listens_for(User, "before_insert")
def _assign_user_numref(_mapper, _connection, target):
    if not target.numref:
        target.numref = f"USR-{datetime.utcnow().year}-{int(uuid.uuid4().int % 1000000):06d}"


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(SqEnum(UserRole), nullable=False, index=True)
    permission = Column(String, nullable=False, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school = relationship("School")
    updated_by = relationship("User")

    __table_args__ = (
        UniqueConstraint("role", "permission", "school_id", name="_role_permission_scope_uc"),
    )


class RoleDefinition(Base):
    __tablename__ = "role_definitions"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    color = Column(String, default="#0F766E", nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_role_key = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school = relationship("School")
    created_by = relationship("User")

    __table_args__ = (
        UniqueConstraint("key", "school_id", name="_role_definition_scope_uc"),
    )


class RolePermissionMatrix(Base):
    __tablename__ = "role_permission_matrix"

    id = Column(Integer, primary_key=True, index=True)
    role_key = Column(String, nullable=False, index=True)
    module = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    permission = Column(String, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school = relationship("School")
    updated_by = relationship("User")

    __table_args__ = (
        UniqueConstraint("role_key", "permission", "school_id", name="_role_permission_matrix_scope_uc"),
    )


class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_key = Column(String, nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    school = relationship("School")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])

    __table_args__ = (
        UniqueConstraint("user_id", "role_key", "school_id", name="_user_role_assignment_uc"),
    )

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Academic Info
    registration_number = Column(String, unique=True, index=True) # Matricule
    date_of_birth = Column(DateTime)
    gender = Column(String) # M/F
    student_address = Column(String, nullable=True) # Added field
    student_address_structured = Column(JSON, nullable=True)
    student_formatted_address = Column(String, nullable=True)
    
    # Parent/Guardian Info
    parent_name = Column(String)
    parent_phone = Column(String)
    parent_phone_country_code = Column(String, nullable=True)
    parent_phone_e164 = Column(String, nullable=True)
    parent_email = Column(String, nullable=True)
    parent_address = Column(String, nullable=True) # Added field
    parent_address_structured = Column(JSON, nullable=True)
    parent_formatted_address = Column(String, nullable=True)
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
    duration_minutes = Column(Integer, nullable=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    lock_scope = Column(String, nullable=True)
    status = Column(String, default="draft", nullable=False)
    generation_batch = Column(String, nullable=True, index=True)
    constraints_snapshot = Column(JSON, nullable=True)
    conflict_status = Column(String, default="clear", nullable=False)
    conflict_details = Column(JSON, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
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


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    content_url = Column(String, nullable=True)
    content_text = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_ = relationship("Class")
    subject = relationship("Subject")
    teacher = relationship("User")
    school = relationship("School")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    instructions = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(SqEnum(AssignmentStatus), default=AssignmentStatus.PUBLISHED, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_ = relationship("Class")
    subject = relationship("Subject")
    teacher = relationship("User")
    school = relationship("School")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    content_text = Column(Text, nullable=True)
    attachment_url = Column(String, nullable=True)
    status = Column(SqEnum(SubmissionStatus), default=SubmissionStatus.SUBMITTED, nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    graded_at = Column(DateTime(timezone=True), nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("StudentProfile")


class ParentStudentLink(Base):
    __tablename__ = "parent_student_links"

    id = Column(Integer, primary_key=True, index=True)
    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    relation = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("User")
    student = relationship("StudentProfile")

    __table_args__ = (
        UniqueConstraint('parent_user_id', 'student_id', name='_parent_student_uc'),
    )

    @property
    def relationship(self):
        return self.relation


class AdministrativeRequest(Base):
    __tablename__ = "administrative_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(SqEnum(AdministrativeRequestType), nullable=False)
    status = Column(SqEnum(AdministrativeRequestStatus), default=AdministrativeRequestStatus.PENDING, nullable=False)
    details = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    handled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    handled_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("StudentProfile")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    handled_by = relationship("User", foreign_keys=[handled_by_id])
    school = relationship("School")


class PartnerCompany(Base):
    __tablename__ = "partner_companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    rccm_number = Column(String, nullable=True)
    tax_number = Column(String, nullable=True)
    industry = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    region = Column(String, nullable=True)
    country = Column(String, nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    hr_manager_name = Column(String, nullable=True)
    hr_manager_role = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    max_simultaneous_interns = Column(Integer, nullable=True)
    website = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    partnership_file_id = Column(Integer, ForeignKey("secure_files.id"), nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)

    school = relationship("School")
    created_by = relationship("User")
    partnership_file = relationship("SecureFile")


class Internship(Base):
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("partner_companies.id"), nullable=True, index=True)
    company_name = Column(String, nullable=False)
    academic_level = Column(String, nullable=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True, index=True)
    program = Column(String, nullable=True)
    training_program = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    objectives = Column(Text, nullable=True)
    service_department = Column(String, nullable=True)
    supervisor_name = Column(String, nullable=True)
    supervisor_role = Column(String, nullable=True)
    supervisor_phone = Column(String, nullable=True)
    supervisor_email = Column(String, nullable=True)
    teacher_ref_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pedagogy_coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    internship_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    weeks_count = Column(Integer, nullable=True)
    expected_schedule = Column(String, nullable=True)
    status = Column(String, default="planned", nullable=False)
    notes = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    final_score = Column(Float, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("StudentProfile")
    company = relationship("PartnerCompany")
    class_ref = relationship("Class")
    teacher_ref = relationship("User", foreign_keys=[teacher_ref_id])
    pedagogy_coordinator = relationship("User", foreign_keys=[pedagogy_coordinator_id])
    internship_manager = relationship("User", foreign_keys=[internship_manager_id])
    school = relationship("School")
    created_by = relationship("User", foreign_keys=[created_by_id])


class InternshipAssignment(Base):
    __tablename__ = "internship_assignments"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False, index=True)
    status = Column(String, default="assigned", nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship")
    student = relationship("StudentProfile")
    school = relationship("School")

    __table_args__ = (
        UniqueConstraint("internship_id", "student_id", name="_internship_student_uc"),
    )


class InternshipDailyFollowUp(Base):
    __tablename__ = "internship_daily_followups"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    presence_status = Column(String, default="present", nullable=False)
    activities = Column(Text, nullable=True)
    tasks_description = Column(Text, nullable=True)
    developed_skills = Column(Text, nullable=True)
    tools_used = Column(Text, nullable=True)
    difficulties = Column(Text, nullable=True)
    supervisor_observation = Column(Text, nullable=True)
    supervisor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship")
    student = relationship("StudentProfile")
    supervisor_user = relationship("User")
    school = relationship("School")


class InternshipLogbookEntry(Base):
    __tablename__ = "internship_logbook_entries"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    tasks_done = Column(Text, nullable=True)
    acquired_skills = Column(Text, nullable=True)
    difficulties = Column(Text, nullable=True)
    proposed_solutions = Column(Text, nullable=True)
    hours_count = Column(Float, nullable=True)
    validation_status = Column(String, default="pending", nullable=False, index=True)
    supervisor_comment = Column(Text, nullable=True)
    validated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime(timezone=True), nullable=True)

    internship = relationship("Internship")
    student = relationship("StudentProfile")
    validated_by = relationship("User")
    school = relationship("School")


class InternshipEvaluation(Base):
    __tablename__ = "internship_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    evaluation_type = Column(String, nullable=False, index=True)
    scores = Column(JSON, nullable=True)
    company_score = Column(Float, nullable=True)
    report_score = Column(Float, nullable=True)
    defense_score = Column(Float, nullable=True)
    practical_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    comments = Column(Text, nullable=True)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship")
    student = relationship("StudentProfile")
    evaluator = relationship("User")
    school = relationship("School")


class InternshipDocument(Base):
    __tablename__ = "internship_documents"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    document_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    secure_file_id = Column(Integer, ForeignKey("secure_files.id"), nullable=True)
    status = Column(String, default="available", nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship")
    student = relationship("StudentProfile")
    secure_file = relationship("SecureFile")
    uploaded_by = relationship("User")
    school = relationship("School")


class SchoolExit(Base):
    __tablename__ = "school_exits"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    reason = Column(String, nullable=False)
    exit_date = Column(DateTime, nullable=False)
    destination = Column(String, nullable=True)
    is_authorized = Column(Boolean, default=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("StudentProfile")
    school = relationship("School")
    created_by = relationship("User")


class StudentOrientation(Base):
    __tablename__ = "student_orientations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    recommended_path = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    decision_date = Column(DateTime, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("StudentProfile")
    school = relationship("School")
    created_by = relationship("User")


class AcademicProgram(Base):
    __tablename__ = "academic_programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    sector = Column(String, nullable=False, index=True)
    level = Column(String, nullable=True, index=True)
    diploma = Column(String, nullable=True)
    duration_years = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    school = relationship("School")


class AdmissionApplication(Base):
    __tablename__ = "admission_applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_name = Column(String, nullable=False, index=True)
    applicant_phone = Column(String, nullable=True)
    applicant_email = Column(String, nullable=True)
    desired_level = Column(String, nullable=True)
    desired_program_id = Column(Integer, ForeignKey("academic_programs.id"), nullable=True)
    status = Column(SqEnum(AdmissionStatus), default=AdmissionStatus.SUBMITTED, nullable=False)
    notes = Column(Text, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    handled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    desired_program = relationship("AcademicProgram")
    school = relationship("School")
    handled_by = relationship("User")


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    exam_type = Column(String, nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("academic_programs.id"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, default="planned", nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_ = relationship("Class")
    program = relationship("AcademicProgram")
    school = relationship("School")
    created_by = relationship("User")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    quantity = Column(Integer, default=0)
    minimum_quantity = Column(Integer, default=0)
    location = Column(String, nullable=True)
    status = Column(SqEnum(InventoryStatus), default=InventoryStatus.AVAILABLE, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school = relationship("School")


class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id = Column(Integer, primary_key=True, index=True)
    staff_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period = Column(String, nullable=False, index=True)
    gross_amount = Column(Float, nullable=False)
    deductions = Column(Float, default=0)
    net_amount = Column(Float, nullable=False)
    status = Column(SqEnum(PayrollStatus), default=PayrollStatus.DRAFT, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    staff = relationship("User", foreign_keys=[staff_user_id])
    school = relationship("School")
    created_by = relationship("User", foreign_keys=[created_by_id])


class TransportRoute(Base):
    __tablename__ = "transport_routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    vehicle_identifier = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    driver_phone = Column(String, nullable=True)
    stops = Column(JSON, nullable=True)
    monthly_fee = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    school = relationship("School")


class CanteenMealPlan(Base):
    __tablename__ = "canteen_meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    day_of_week = Column(String, nullable=True)
    meal_type = Column(String, nullable=False)
    menu = Column(Text, nullable=True)
    price = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    school = relationship("School")

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

class StudentInvoiceStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"

class GeneratedDocumentType(str, enum.Enum):
    RECEIPT = "receipt"
    CERTIFICATE = "certificate"
    REPORT_CARD = "report_card"
    INVOICE = "invoice"
    TRANSCRIPT = "transcript"
    DIPLOMA = "diploma"
    OTHER = "other"

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


class StudentInvoice(Base):
    __tablename__ = "student_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0, nullable=False)
    remaining_balance = Column(Float, default=0, nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(SqEnum(StudentInvoiceStatus), default=StudentInvoiceStatus.UNPAID, nullable=False)
    source_type = Column(String, default="fee", nullable=False, index=True)
    source_id = Column(Integer, nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    fee_id = Column(Integer, ForeignKey("fees.id"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("StudentProfile")
    fee = relationship("Fee")
    school = relationship("School")
    created_by = relationship("User")


class OutstandingBalance(Base):
    __tablename__ = "outstanding_balances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("student_invoices.id"), nullable=True, index=True)
    fee_id = Column(Integer, ForeignKey("fees.id"), nullable=True, index=True)
    due_date = Column(DateTime, nullable=True)
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0, nullable=False)
    remaining_balance = Column(Float, default=0, nullable=False)
    status = Column(SqEnum(StudentInvoiceStatus), default=StudentInvoiceStatus.UNPAID, nullable=False)
    last_payment_at = Column(DateTime(timezone=True), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("StudentProfile")
    invoice = relationship("StudentInvoice")
    fee = relationship("Fee")
    school = relationship("School")


class CashJournalEntry(Base):
    __tablename__ = "cash_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    entry_type = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reference = Column(String, nullable=True, index=True)
    description = Column(String, nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payment = relationship("Payment")
    expense = relationship("Expense")
    student = relationship("StudentProfile")
    operator = relationship("User")
    school = relationship("School")


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(SqEnum(GeneratedDocumentType), nullable=False, index=True)
    title = Column(String, nullable=False)
    reference = Column(String, nullable=True, index=True)
    source_type = Column(String, nullable=True, index=True)
    source_id = Column(Integer, nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=True)
    content = Column(JSON, nullable=True)
    download_url = Column(String, nullable=True)
    generated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    downloaded_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("StudentProfile")
    parent = relationship("User", foreign_keys=[parent_user_id])
    school = relationship("School")
    academic_year = relationship("AcademicYear")
    generated_by = relationship("User", foreign_keys=[generated_by_id])


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    recipient_name = Column(String, nullable=True)
    recipient_contact = Column(String, nullable=True)
    channel = Column(String, nullable=False, default="system")
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="recorded", nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    source_type = Column(String, nullable=True, index=True)
    source_id = Column(Integer, nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recipient = relationship("User", foreign_keys=[recipient_user_id])
    student = relationship("StudentProfile")
    school = relationship("School")
    created_by = relationship("User", foreign_keys=[created_by_id])


class FinancialReportSnapshot(Base):
    __tablename__ = "financial_report_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    period_key = Column(String, nullable=False, index=True)
    total_invoiced = Column(Float, default=0, nullable=False)
    total_paid = Column(Float, default=0, nullable=False)
    total_expenses = Column(Float, default=0, nullable=False)
    total_outstanding = Column(Float, default=0, nullable=False)
    cash_total = Column(Float, default=0, nullable=False)
    payload = Column(JSON, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school = relationship("School")


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


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class NotificationChannel(str, enum.Enum):
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"

class NotificationStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    current_step = Column(Integer, default=1)
    status = Column(SqEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    decided_at = Column(DateTime(timezone=True), nullable=True)

    school = relationship("School")
    requested_by = relationship("User")
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    role = Column(SqEnum(UserRole), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(SqEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    comment = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    approver = relationship("User")


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    academic_year = relationship("AcademicYear")
    school = relationship("School")


class CourseUnit(Base):
    __tablename__ = "course_units"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    credits = Column(Float, default=0)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("academic_programs.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    semester = relationship("Semester")
    program = relationship("AcademicProgram")
    teacher = relationship("User")
    school = relationship("School")


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    course_unit_id = Column(Integer, ForeignKey("course_units.id"), nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)
    status = Column(String, default="registered", nullable=False)
    score = Column(Float, nullable=True)
    grade = Column(String, nullable=True)
    grade_point = Column(Float, nullable=True)
    credits_attempted = Column(Float, default=0)
    credits_validated = Column(Float, default=0)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    registered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("StudentProfile")
    course_unit = relationship("CourseUnit")
    semester = relationship("Semester")
    school = relationship("School")
    registered_by = relationship("User")

    __table_args__ = (
        UniqueConstraint("student_id", "course_unit_id", name="_student_course_unit_uc"),
    )


class UniversityScheduleSlot(Base):
    __tablename__ = "university_schedule_slots"

    id = Column(Integer, primary_key=True, index=True)
    course_unit_id = Column(Integer, ForeignKey("course_units.id"), nullable=False)
    day_of_week = Column(SqEnum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room = Column(String, nullable=True)
    group_name = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    course_unit = relationship("CourseUnit")
    school = relationship("School")


class DiplomaRecord(Base):
    __tablename__ = "diploma_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("academic_programs.id"), nullable=True)
    diploma_name = Column(String, nullable=False)
    mention = Column(String, nullable=True)
    issued_date = Column(DateTime, nullable=True)
    certificate_number = Column(String, unique=True, nullable=False)
    total_credits = Column(Float, default=0)
    is_certified = Column(Boolean, default=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    issued_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    student = relationship("StudentProfile")
    program = relationship("AcademicProgram")
    school = relationship("School")
    issued_by = relationship("User")


class CertifiedTranscript(Base):
    __tablename__ = "certified_transcripts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=True)
    total_credits = Column(Float, default=0)
    gpa = Column(Float, nullable=True)
    content = Column(JSON, nullable=True)
    certificate_number = Column(String, unique=True, nullable=False)
    is_certified = Column(Boolean, default=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    issued_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("StudentProfile")
    semester = relationship("Semester")
    school = relationship("School")
    issued_by = relationship("User")


class StaffContract(Base):
    __tablename__ = "staff_contracts"

    id = Column(Integer, primary_key=True, index=True)
    staff_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_type = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    base_salary = Column(Float, default=0)
    cnss_number = Column(String, nullable=True)
    tax_identifier = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    staff = relationship("User")
    school = relationship("School")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    staff_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(SqEnum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    decided_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    staff = relationship("User", foreign_keys=[staff_user_id])
    school = relationship("School")
    decided_by = relationship("User", foreign_keys=[decided_by_id])


class PayrollAdjustment(Base):
    __tablename__ = "payroll_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    payroll_record_id = Column(Integer, ForeignKey("payroll_records.id"), nullable=False)
    adjustment_type = Column(String, nullable=False)
    label = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    is_taxable = Column(Boolean, default=True)

    payroll_record = relationship("PayrollRecord")


class TransportAssignment(Base):
    __tablename__ = "transport_assignments"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("transport_routes.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    pickup_stop = Column(String, nullable=True)
    dropoff_stop = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    route = relationship("TransportRoute")
    student = relationship("StudentProfile")
    school = relationship("School")


class CanteenSubscription(Base):
    __tablename__ = "canteen_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("canteen_meal_plans.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    meal_plan = relationship("CanteenMealPlan")
    student = relationship("StudentProfile")
    school = relationship("School")


class CanteenAttendance(Base):
    __tablename__ = "canteen_attendance"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("canteen_subscriptions.id"), nullable=False)
    served_at = Column(DateTime(timezone=True), server_default=func.now())
    served_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    subscription = relationship("CanteenSubscription")
    served_by = relationship("User")
    school = relationship("School")


class ChartAccount(Base):
    __tablename__ = "chart_accounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    school = relationship("School")


class VendorInvoice(Base):
    __tablename__ = "vendor_invoices"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String, nullable=False)
    invoice_number = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(SqEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    account_id = Column(Integer, ForeignKey("chart_accounts.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("ChartAccount")
    school = relationship("School")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    direction = Column(String, nullable=False)
    account_id = Column(Integer, ForeignKey("chart_accounts.id"), nullable=True)
    reference = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    account = relationship("ChartAccount")
    school = relationship("School")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(DateTime, nullable=False, index=True)
    reference = Column(String, nullable=True, index=True)
    description = Column(String, nullable=False)
    source_type = Column(String, nullable=True, index=True)
    source_id = Column(Integer, nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    school = relationship("School")
    created_by = relationship("User")
    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("chart_accounts.id"), nullable=False)
    label = Column(String, nullable=True)
    debit = Column(Float, default=0, nullable=False)
    credit = Column(Float, default=0, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartAccount")
    school = relationship("School")


class BankReconciliation(Base):
    __tablename__ = "bank_reconciliations"

    id = Column(Integer, primary_key=True, index=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=False)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    matched_amount = Column(Float, nullable=False)
    status = Column(String, default="matched", nullable=False)
    notes = Column(Text, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    reconciled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reconciled_at = Column(DateTime(timezone=True), server_default=func.now())

    bank_transaction = relationship("BankTransaction")
    journal_entry = relationship("JournalEntry")
    school = relationship("School")
    reconciled_by = relationship("User")


class GovernmentExport(Base):
    __tablename__ = "government_exports"

    id = Column(Integer, primary_key=True, index=True)
    export_type = Column(String, nullable=False, index=True)
    period = Column(String, nullable=True)
    payload = Column(JSON, nullable=False)
    generated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    generated_by = relationship("User")
    school = relationship("School")


class NotificationProvider(Base):
    __tablename__ = "notification_providers"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(SqEnum(NotificationChannel), nullable=False)
    provider_name = Column(String, nullable=False)
    api_key_secret = Column(String, nullable=True)
    sender_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

    school = relationship("School")


class NotificationMessage(Base):
    __tablename__ = "notification_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(SqEnum(NotificationChannel), nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    provider_id = Column(Integer, ForeignKey("notification_providers.id"), nullable=True)
    status = Column(SqEnum(NotificationStatus), default=NotificationStatus.QUEUED, nullable=False)
    provider_response = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    template_key = Column(String, nullable=True, index=True)
    locale = Column(String, default="fr", nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    provider = relationship("NotificationProvider")
    school = relationship("School")
    created_by = relationship("User")


class AIProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    provider_type = Column(String, nullable=False, index=True)
    api_key_encrypted = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    default_model = Column(String, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    priority = Column(Integer, default=100, nullable=False, index=True)
    cost_per_1k_input_tokens = Column(Float, default=0, nullable=False)
    cost_per_1k_output_tokens = Column(Float, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AICreditPack(Base):
    __tablename__ = "ai_credit_packs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    credits_amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="FCFA", nullable=False, index=True)
    country_code = Column(String, default="CI", nullable=False, index=True)
    region = Column(String, default="africa", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    validity_days = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AIWallet(Base):
    __tablename__ = "ai_wallets"

    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    balance_credits = Column(Integer, default=0, nullable=False)
    total_purchased_credits = Column(Integer, default=0, nullable=False)
    total_used_credits = Column(Integer, default=0, nullable=False)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    school = relationship("School")

    __table_args__ = (
        UniqueConstraint("owner_type", "user_id", "school_id", name="_ai_wallet_owner_uc"),
    )


class PlatformPayment(Base):
    __tablename__ = "platform_payments"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, nullable=False, unique=True, index=True)
    payer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    payment_type = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, index=True)
    country_code = Column(String, nullable=True, index=True)
    region = Column(String, nullable=True, index=True)
    provider = Column(String, nullable=False, index=True)
    provider_reference = Column(String, nullable=True, index=True)
    status = Column(String, default="pending", nullable=False, index=True)
    beneficiary_entity = Column(String, nullable=False, index=True)
    pack_id = Column(Integer, ForeignKey("ai_credit_packs.id"), nullable=True)
    credits_amount = Column(Integer, default=0, nullable=False)
    wallet_id = Column(Integer, ForeignKey("ai_wallets.id"), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    payer = relationship("User")
    school = relationship("School")
    pack = relationship("AICreditPack")
    wallet = relationship("AIWallet")


class AICreditTransaction(Base):
    __tablename__ = "ai_credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("ai_wallets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    transaction_type = Column(String, nullable=False, index=True)
    credits_amount = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    payment_id = Column(Integer, ForeignKey("platform_payments.id"), nullable=True, index=True)
    usage_log_id = Column(Integer, ForeignKey("ai_usage_logs.id"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("AIWallet")
    user = relationship("User")
    school = relationship("School")
    payment = relationship("PlatformPayment")


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    wallet_id = Column(Integer, ForeignKey("ai_wallets.id"), nullable=True, index=True)
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=True)
    model_name = Column(String, nullable=True, index=True)
    module_name = Column(String, nullable=True, index=True)
    action_type = Column(String, nullable=True, index=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    credits_charged = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Float, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    request_summary = Column(Text, nullable=True)
    status = Column(String, default="successful", nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    school = relationship("School")
    wallet = relationship("AIWallet")
    provider = relationship("AIProvider")


class SchoolPaymentAccount(Base):
    __tablename__ = "school_payment_accounts"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    account_name = Column(String, nullable=False)
    merchant_id = Column(String, nullable=True)
    api_key_encrypted = Column(String, nullable=True)
    secret_key_encrypted = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    country_code = Column(String, default="CI", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school = relationship("School")


class SchoolPayment(Base):
    __tablename__ = "school_payments"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, nullable=False, unique=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    payer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("student_invoices.id"), nullable=True, index=True)
    payment_type = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    provider_reference = Column(String, nullable=True, index=True)
    school_beneficiary_account_id = Column(Integer, ForeignKey("school_payment_accounts.id"), nullable=True)
    status = Column(String, default="pending", nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school = relationship("School")
    payer = relationship("User")
    student = relationship("StudentProfile")
    invoice = relationship("StudentInvoice")
    beneficiary_account = relationship("SchoolPaymentAccount")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=True, index=True)
    entity_id = Column(String, nullable=True, index=True)
    method = Column(String, nullable=True)
    path = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    school = relationship("School")
    actor = relationship("User")


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    severity = Column(String, default="info", nullable=False, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    school = relationship("School")
    actor = relationship("User")


class SecureFile(Base):
    __tablename__ = "secure_files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    display_name = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)
    stored_filename = Column(String, nullable=False, unique=True, index=True)
    content_type = Column(String, nullable=False)
    file_extension = Column(String, nullable=True, index=True)
    size_bytes = Column(Integer, nullable=False)
    checksum_sha256 = Column(String, nullable=False, index=True)
    storage_backend = Column(String, default="local", nullable=False)
    storage_path = Column(String, nullable=False)
    entity_type = Column(String, nullable=True, index=True)
    entity_id = Column(String, nullable=True, index=True)
    status = Column(String, default="active", nullable=False, index=True)
    visibility = Column(String, default="private", nullable=False, index=True)
    is_shareable = Column(Boolean, default=False, nullable=False)
    approval_status = Column(String, default="approved", nullable=False, index=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    download_limit = Column(Integer, nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    scan_status = Column(String, default="not_configured", nullable=False, index=True)
    scan_details = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    school = relationship("School")
    uploaded_by = relationship(
    "User",
    foreign_keys=[uploaded_by_id],
)
    approved_by = relationship(
    "User",
    foreign_keys=[approved_by_id],
)


class DocumentShare(Base):
    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("secure_files.id"), nullable=False, index=True)
    share_type = Column(String, nullable=False, index=True)
    mode = Column(String, nullable=False, default="private", index=True)
    can_reshare = Column(Boolean, default=False, nullable=False)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    recipient_school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    recipient_numref = Column(String, nullable=True, index=True)
    status = Column(String, default="active", nullable=False, index=True)
    encrypted_token = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    download_limit = Column(Integer, nullable=True)
    download_count = Column(Integer, default=0, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    file = relationship("SecureFile")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id])
    recipient_school = relationship("School", foreign_keys=[recipient_school_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    school = relationship("School", foreign_keys=[school_id])


class DataConsent(Base):
    __tablename__ = "data_consents"

    id = Column(Integer, primary_key=True, index=True)
    subject_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(String, nullable=False, index=True)
    granted = Column(Boolean, default=True, nullable=False)
    source = Column(String, nullable=True)
    locale = Column(String, default="fr", nullable=False)
    policy_version = Column(String, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    subject_user = relationship("User", foreign_keys=[subject_user_id])
    school = relationship("School")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])


class DataRetentionRule(Base):
    __tablename__ = "data_retention_rules"

    id = Column(Integer, primary_key=True, index=True)
    data_category = Column(String, nullable=False, index=True)
    retention_days = Column(Integer, nullable=False)
    legal_basis = Column(String, nullable=True)
    action = Column(String, default="review", nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school = relationship("School")
    created_by = relationship("User")
