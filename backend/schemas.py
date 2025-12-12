from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, time, date
from .models import UserRole, SchoolType, DayOfWeek, AttendanceStatus

# School Schemas
class SchoolBase(BaseModel):
    name: str
    domain_prefix: str
    school_type: SchoolType = SchoolType.GENERAL
    address: Optional[str] = None

class SchoolCreate(SchoolBase):
    pass

class SchoolResponse(SchoolBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole

class UserCreate(UserBase):
    password: str
    school_domain_prefix: Optional[str] = None # For joining an existing school

class UserResponse(UserBase):
    id: int
    is_active: bool
    school_id: Optional[int]
    
    class Config:
        from_attributes = True

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Student Schemas
class StudentProfileBase(BaseModel):
    registration_number: str
    date_of_birth: datetime
    gender: str
    student_address: Optional[str] = None
    parent_name: str
    parent_phone: str
    parent_email: Optional[EmailStr] = None
    parent_address: Optional[str] = None
    current_class_id: Optional[int] = None

class StudentCreateSchema(UserCreate):
    profile: StudentProfileBase

class StudentUpdateProfile(BaseModel):
    registration_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    student_address: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    parent_address: Optional[str] = None
    current_class_id: Optional[int] = None

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile: Optional[StudentUpdateProfile] = None

class StudentProfileResponse(StudentProfileBase):
    id: int
    class Config:
        from_attributes = True

class StudentResponse(UserResponse):
    student_profile: Optional[StudentProfileResponse] = None

# Teacher Schemas
class TeacherProfileBase(BaseModel):
    specialization: Optional[str] = None
    join_date: Optional[datetime] = None
    bio: Optional[str] = None

class TeacherCreate(UserCreate):
    profile: TeacherProfileBase

class TeacherUpdateProfile(BaseModel):
    specialization: Optional[str] = None
    join_date: Optional[datetime] = None
    bio: Optional[str] = None

class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    profile: Optional[TeacherUpdateProfile] = None

class TeacherProfileResponse(TeacherProfileBase):
    id: int
    class Config:
        from_attributes = True

class TeacherResponse(UserResponse):
    phone_number: Optional[str] = None
    address: Optional[str] = None
    teacher_profile: Optional[TeacherProfileResponse] = None

# Academic Year & Term Schemas

class TermBase(BaseModel):
    name: str # e.g. "Trimester 1"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    academic_year_id: int

class TermCreate(TermBase):
    pass

class TermResponse(TermBase):
    id: int
    class Config:
        from_attributes = True

class AcademicYearBase(BaseModel):
    name: str # e.g. "2024-2025"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = False

class AcademicYearCreate(AcademicYearBase):
    pass

class AcademicYearResponse(AcademicYearBase):
    id: int
    school_id: int
    terms: List[TermResponse] = []
    
    class Config:
        from_attributes = True

# Class Schemas
class ClassBase(BaseModel):
    name: str
    level: Optional[str] = None
    main_teacher_id: Optional[int] = None

class ClassCreate(ClassBase):
    pass

class ClassResponse(ClassBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

# Subject Schemas
class SubjectBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    coefficient: int = 1

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    coefficient: Optional[int] = None

class SubjectResponse(SubjectBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

# Timetable Schemas
class TimetableBase(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    room: Optional[str] = None
    class_id: int
    subject_id: int
    teacher_id: Optional[int] = None

class TimetableCreate(TimetableBase):
    pass

class TimetableResponse(TimetableBase):
    id: int
    
    class Config:
        from_attributes = True

# Grade & Assessment Schemas

class AssessmentBase(BaseModel):
    title: str
    type: str # Enum via AssessmentType
    date: datetime
    max_score: float = 20.0
    weight: int = 1
    class_id: int
    subject_id: int
    term_id: int

class AssessmentCreate(AssessmentBase):
    pass

class AssessmentResponse(AssessmentBase):
    id: int
    
    class Config:
        from_attributes = True

class GradeBase(BaseModel):
    score: float
    comment: Optional[str] = None
    assessment_id: int
    student_id: int

class GradeCreate(GradeBase):
    pass

class GradeResponse(GradeBase):
    id: int
    
    class Config:
        from_attributes = True

class GradeBulkCreate(BaseModel):
    assessment_id: int
    grades: List[GradeCreate] # Or a simplified object: {student_id: int, score: float, comment: str}

class ReportAssessment(BaseModel):
    assessment: str
    score: float
    max: float
    weight: int

class ReportSubject(BaseModel):
    subject: str
    assessments: List[ReportAssessment]
    average: float

class ReportCardResponse(BaseModel):
    student_id: int
    term_id: Optional[int] = None
    subjects: List[ReportSubject]
    overall_average: float


# Attendance Schemas
class AttendanceBase(BaseModel):
    date: datetime
    status: AttendanceStatus
    remarks: Optional[str] = None
    student_id: int
    timetable_id: int

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    id: int
    recorded_by_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AttendanceBatchCreate(BaseModel):
    timetable_id: int
    date: datetime
    records: List[AttendanceCreate] # Actually specific per student

class AttendanceStudentUpdate(BaseModel):
    student_id: int
    status: AttendanceStatus
    remarks: Optional[str] = None

class AttendanceBatchUpdate(BaseModel):
    timetable_id: int
    date: datetime
    students: List[AttendanceStudentUpdate]
    
class AttendanceStats(BaseModel):
    total: int
    present: int
    absent: int
    late: int
    excused: int


