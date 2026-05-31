from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, time, date
from .models import (
    UserRole,
    SchoolType,
    DayOfWeek,
    AttendanceStatus,
    BookStatus,
    LoanStatus,
    FeeStatus,
    ExpenseCategory,
    StudentStatus,
    CertificateType,
    CertificateStatus,
    CashClosureStatus,
    AssignmentStatus,
    SubmissionStatus,
    AdministrativeRequestType,
    AdministrativeRequestStatus,
    AdmissionStatus,
    InventoryStatus,
    PayrollStatus,
    ApprovalStatus,
    NotificationChannel,
    NotificationStatus,
    LeaveStatus,
    InvoiceStatus,
)

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
    
    model_config = ConfigDict(from_attributes=True)

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
    school: Optional[SchoolResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role: UserRole
    is_active: Optional[bool] = None

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
    guardian_relation: Optional[str] = None
    status: StudentStatus = StudentStatus.UNASSIGNED
    previous_level: Optional[str] = None
    previous_class: Optional[str] = None
    current_class_id: Optional[int] = None

class EducationHistoryBase(BaseModel):
    previous_school: str
    class_level: str
    degree_obtained: Optional[str] = None
    grade_average: Optional[str] = None
    year_completed: Optional[int] = None

class EducationHistoryCreate(EducationHistoryBase):
    pass

class EducationHistoryResponse(EducationHistoryBase):
    id: int
    student_id: int
    
    model_config = ConfigDict(from_attributes=True)

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
    guardian_relation: Optional[str] = None
    status: Optional[StudentStatus] = None
    previous_level: Optional[str] = None
    previous_class: Optional[str] = None
    current_class_id: Optional[int] = None

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile: Optional[StudentUpdateProfile] = None

class StudentProfileResponse(StudentProfileBase):
    id: int
    education_history: List[EducationHistoryResponse] = []
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

class GradeBase(BaseModel):
    score: float
    comment: Optional[str] = None
    assessment_id: int
    student_id: int

class GradeCreate(GradeBase):
    pass

class GradeResponse(GradeBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class GradeBulkCreate(BaseModel):
    assessment_id: int
    grades: List[GradeCreate] # Or a simplified object: {student_id: int, score: float, comment: str}

class ReportAssessment(BaseModel):
    assessment: str
    score: float
    max: float
    weight: int

class ReportSubject(BaseModel):
    subject_id: int
    subject_name: str
    coefficient: int
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
    
    model_config = ConfigDict(from_attributes=True)

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
    excused: int
    
    
# Library Management Schemas

# Books
class BookBase(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    category: Optional[str] = None
    quantity: int = 1
    location: Optional[str] = None
    
class BookCreate(BookBase):
    school_id: Optional[int] = None
    
class BookResponse(BookBase):
    id: int
    available_quantity: int
    school_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Loans
class LoanBase(BaseModel):
    book_id: int
    user_id: int
    due_date: datetime
    notes: Optional[str] = None

class LoanCreate(LoanBase):
    pass
    
class LoanResponse(LoanBase):
    id: int
    issue_date: datetime
    return_date: Optional[datetime] = None
    status: LoanStatus
    
    # Include related data for display
    book_title: Optional[str] = None
    user_full_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Finance Management Schemas

class PaymentCreate(BaseModel):
    amount: float
    payment_date: Optional[datetime] = None
    note: Optional[str] = None
    operator_station: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    amount: float
    payment_date: datetime
    note: Optional[str] = None
    receipt_number: Optional[str] = None
    operator_station: Optional[str] = None
    recorded_by_id: Optional[int] = None
    fee_id: int

    model_config = ConfigDict(from_attributes=True)


class FeeBase(BaseModel):
    title: str
    amount: float
    due_date: Optional[datetime] = None
    status: FeeStatus = FeeStatus.PENDING
    description: Optional[str] = None
    category: Optional[str] = None
    category_order: int = 0
    is_required: bool = True
    academic_year_id: Optional[int] = None
    class_id: Optional[int] = None
    covered_by: Optional[List[dict]] = None
    student_id: Optional[int] = None


class FeeCreate(FeeBase):
    school_id: Optional[int] = None


class FeeResponse(FeeBase):
    id: int
    school_id: Optional[int] = None
    created_at: datetime
    payments: List[PaymentResponse] = []
    total_paid: float = 0
    remaining_balance: float = 0

    model_config = ConfigDict(from_attributes=True)


class FeeScheduleBase(BaseModel):
    name: str
    amount: float
    category_order: int = 0
    is_required: bool = True
    is_current: bool = True
    academic_year_id: Optional[int] = None
    class_id: Optional[int] = None
    level: Optional[str] = None


class FeeScheduleCreate(FeeScheduleBase):
    school_id: Optional[int] = None


class FeeScheduleResponse(FeeScheduleBase):
    id: int
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationDocumentBase(BaseModel):
    name: str
    is_received: bool = False
    notes: Optional[str] = None


class RegistrationDocumentUpdate(RegistrationDocumentBase):
    pass


class RegistrationDocumentResponse(RegistrationDocumentBase):
    id: int
    student_id: int
    received_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateCreate(BaseModel):
    certificate_type: CertificateType


class CertificateResponse(BaseModel):
    id: int
    certificate_type: CertificateType
    status: CertificateStatus
    blocked_reason: Optional[str] = None
    content: Optional[str] = None
    student_id: int
    school_id: int
    generated_by_id: Optional[int] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashClosureCreate(BaseModel):
    closure_date: datetime
    counted_amount: float
    notes: Optional[str] = None


class CashClosureResponse(BaseModel):
    id: int
    closure_date: datetime
    counted_amount: float
    expected_amount: float
    difference: float
    status: CashClosureStatus
    notes: Optional[str] = None
    school_id: int
    submitted_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    created_at: datetime
    approved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetForecastBase(BaseModel):
    expected_students: int = 0
    expected_revenue: float = 0
    fee_category: Optional[str] = None
    level: Optional[str] = None
    academic_year_id: Optional[int] = None
    class_id: Optional[int] = None


class BudgetForecastCreate(BudgetForecastBase):
    school_id: Optional[int] = None


class BudgetForecastResponse(BudgetForecastBase):
    id: int
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SmsMessageCreate(BaseModel):
    recipient_phone: str
    recipient_name: Optional[str] = None
    event_type: str
    message: str
    student_id: Optional[int] = None


class SmsMessageResponse(SmsMessageCreate):
    id: int
    school_id: int
    status: str
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Pedagogy and Portal Schemas

class CourseMaterialCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    class_id: int
    subject_id: Optional[int] = None


class CourseMaterialResponse(CourseMaterialCreate):
    id: int
    teacher_id: Optional[int] = None
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentCreate(BaseModel):
    title: str
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    status: AssignmentStatus = AssignmentStatus.PUBLISHED
    class_id: int
    subject_id: Optional[int] = None


class AssignmentResponse(AssignmentCreate):
    id: int
    teacher_id: Optional[int] = None
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentSubmissionCreate(BaseModel):
    content_text: Optional[str] = None
    attachment_url: Optional[str] = None


class AssignmentSubmissionGrade(BaseModel):
    score: Optional[float] = None
    feedback: Optional[str] = None


class AssignmentSubmissionResponse(AssignmentSubmissionCreate):
    id: int
    assignment_id: int
    student_id: int
    status: SubmissionStatus
    score: Optional[float] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    graded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ParentStudentLinkCreate(BaseModel):
    parent_user_id: int
    student_id: int
    relationship: Optional[str] = None


class ParentStudentLinkResponse(ParentStudentLinkCreate):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdministrativeRequestCreate(BaseModel):
    request_type: AdministrativeRequestType
    student_id: int
    details: Optional[str] = None


class AdministrativeRequestUpdate(BaseModel):
    status: AdministrativeRequestStatus
    response: Optional[str] = None


class AdministrativeRequestResponse(BaseModel):
    id: int
    request_type: AdministrativeRequestType
    status: AdministrativeRequestStatus
    details: Optional[str] = None
    response: Optional[str] = None
    student_id: int
    requested_by_id: Optional[int] = None
    handled_by_id: Optional[int] = None
    school_id: int
    created_at: datetime
    handled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InternshipCreate(BaseModel):
    student_id: int
    company_name: str
    supervisor_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "planned"
    notes: Optional[str] = None


class InternshipResponse(InternshipCreate):
    id: int
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchoolExitCreate(BaseModel):
    student_id: int
    reason: str
    exit_date: datetime
    destination: Optional[str] = None
    is_authorized: bool = False


class SchoolExitResponse(SchoolExitCreate):
    id: int
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentOrientationCreate(BaseModel):
    student_id: int
    recommended_path: str
    notes: Optional[str] = None
    decision_date: Optional[datetime] = None


class StudentOrientationResponse(StudentOrientationCreate):
    id: int
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Institution Operations Schemas

class AcademicProgramCreate(BaseModel):
    name: str
    sector: str
    level: Optional[str] = None
    diploma: Optional[str] = None
    duration_years: Optional[int] = None
    description: Optional[str] = None


class AcademicProgramResponse(AcademicProgramCreate):
    id: int
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdmissionApplicationCreate(BaseModel):
    applicant_name: str
    applicant_phone: Optional[str] = None
    applicant_email: Optional[str] = None
    desired_level: Optional[str] = None
    desired_program_id: Optional[int] = None
    status: AdmissionStatus = AdmissionStatus.SUBMITTED
    notes: Optional[str] = None


class AdmissionApplicationUpdate(BaseModel):
    status: AdmissionStatus
    notes: Optional[str] = None


class AdmissionApplicationResponse(AdmissionApplicationCreate):
    id: int
    school_id: int
    handled_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExamSessionCreate(BaseModel):
    name: str
    exam_type: str
    class_id: Optional[int] = None
    program_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "planned"


class ExamSessionResponse(ExamSessionCreate):
    id: int
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryItemCreate(BaseModel):
    name: str
    category: str
    quantity: int = 0
    minimum_quantity: int = 0
    location: Optional[str] = None


class InventoryItemResponse(InventoryItemCreate):
    id: int
    status: InventoryStatus
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayrollRecordCreate(BaseModel):
    staff_user_id: int
    period: str
    gross_amount: float
    deductions: float = 0


class PayrollRecordUpdate(BaseModel):
    status: PayrollStatus


class PayrollRecordResponse(PayrollRecordCreate):
    id: int
    net_amount: float
    status: PayrollStatus
    paid_at: Optional[datetime] = None
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransportRouteCreate(BaseModel):
    name: str
    vehicle_identifier: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    stops: Optional[List[str]] = None
    monthly_fee: float = 0
    is_active: bool = True


class TransportRouteResponse(TransportRouteCreate):
    id: int
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CanteenMealPlanCreate(BaseModel):
    name: str
    day_of_week: Optional[str] = None
    meal_type: str
    menu: Optional[str] = None
    price: float = 0
    is_active: bool = True


class CanteenMealPlanResponse(CanteenMealPlanCreate):
    id: int
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseBase(BaseModel):
    title: str
    amount: float
    category: ExpenseCategory = ExpenseCategory.OTHER
    date: Optional[datetime] = None
    description: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    school_id: Optional[int] = None


class ExpenseResponse(ExpenseBase):
    id: int
    school_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Enterprise Product Schemas

class ApprovalStepCreate(BaseModel):
    step_order: int
    role: UserRole


class ApprovalWorkflowCreate(BaseModel):
    entity_type: str
    entity_id: int
    title: str
    steps: List[ApprovalStepCreate]


class ApprovalWorkflowResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    title: str
    current_step: int
    status: ApprovalStatus
    school_id: int
    created_at: datetime
    decided_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecision(BaseModel):
    status: ApprovalStatus
    comment: Optional[str] = None


class SemesterCreate(BaseModel):
    name: str
    code: str
    academic_year_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SemesterResponse(SemesterCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class CourseUnitCreate(BaseModel):
    code: str
    name: str
    credits: float = 0
    semester_id: Optional[int] = None
    program_id: Optional[int] = None
    teacher_id: Optional[int] = None


class CourseUnitResponse(CourseUnitCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class UniversityScheduleSlotCreate(BaseModel):
    course_unit_id: int
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    room: Optional[str] = None
    group_name: Optional[str] = None


class UniversityScheduleSlotResponse(UniversityScheduleSlotCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class DiplomaRecordCreate(BaseModel):
    student_id: int
    diploma_name: str
    certificate_number: str
    program_id: Optional[int] = None
    mention: Optional[str] = None
    issued_date: Optional[datetime] = None
    total_credits: float = 0
    is_certified: bool = False


class DiplomaRecordResponse(DiplomaRecordCreate):
    id: int
    school_id: int
    issued_by_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class CertifiedTranscriptCreate(BaseModel):
    student_id: int
    certificate_number: str
    semester_id: Optional[int] = None
    total_credits: float = 0
    gpa: Optional[float] = None
    content: Optional[dict] = None


class CertifiedTranscriptResponse(CertifiedTranscriptCreate):
    id: int
    is_certified: bool
    school_id: int
    issued_by_id: Optional[int] = None
    issued_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StaffContractCreate(BaseModel):
    staff_user_id: int
    contract_type: str
    start_date: datetime
    end_date: Optional[datetime] = None
    base_salary: float = 0
    cnss_number: Optional[str] = None
    tax_identifier: Optional[str] = None
    status: str = "active"


class StaffContractResponse(StaffContractCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class LeaveRequestCreate(BaseModel):
    staff_user_id: int
    leave_type: str
    start_date: datetime
    end_date: datetime
    reason: Optional[str] = None


class LeaveRequestResponse(LeaveRequestCreate):
    id: int
    status: LeaveStatus
    school_id: int
    decided_by_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class PayrollAdjustmentCreate(BaseModel):
    payroll_record_id: int
    adjustment_type: str
    label: str
    amount: float
    is_taxable: bool = True


class PayrollAdjustmentResponse(PayrollAdjustmentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TransportAssignmentCreate(BaseModel):
    route_id: int
    student_id: int
    pickup_stop: Optional[str] = None
    dropoff_stop: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True


class TransportAssignmentResponse(TransportAssignmentCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class CanteenSubscriptionCreate(BaseModel):
    meal_plan_id: int
    student_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True


class CanteenSubscriptionResponse(CanteenSubscriptionCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class CanteenAttendanceCreate(BaseModel):
    subscription_id: int


class CanteenAttendanceResponse(CanteenAttendanceCreate):
    id: int
    served_at: datetime
    served_by_id: Optional[int] = None
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class ChartAccountCreate(BaseModel):
    code: str
    name: str
    account_type: str


class ChartAccountResponse(ChartAccountCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class VendorInvoiceCreate(BaseModel):
    vendor_name: str
    invoice_number: str
    amount: float
    due_date: Optional[datetime] = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    account_id: Optional[int] = None


class VendorInvoiceResponse(VendorInvoiceCreate):
    id: int
    school_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BankTransactionCreate(BaseModel):
    transaction_date: datetime
    description: str
    amount: float
    direction: str
    account_id: Optional[int] = None
    reference: Optional[str] = None


class BankTransactionResponse(BankTransactionCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class GovernmentExportCreate(BaseModel):
    export_type: str
    period: Optional[str] = None


class GovernmentExportResponse(BaseModel):
    id: int
    export_type: str
    period: Optional[str] = None
    payload: dict
    generated_by_id: Optional[int] = None
    school_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NotificationProviderCreate(BaseModel):
    channel: NotificationChannel
    provider_name: str
    api_key_secret: Optional[str] = None
    sender_id: Optional[str] = None
    is_active: bool = True


class NotificationProviderResponse(NotificationProviderCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class NotificationMessageCreate(BaseModel):
    channel: NotificationChannel
    recipient: str
    message: str
    subject: Optional[str] = None
    provider_id: Optional[int] = None


class NotificationMessageResponse(NotificationMessageCreate):
    id: int
    status: NotificationStatus
    provider_response: Optional[str] = None
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


