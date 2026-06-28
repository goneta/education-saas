from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, time, date
from urllib.parse import urlparse
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
class InternationalAddress(BaseModel):
    street: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    formatted: Optional[str] = None


def _validate_http_url(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return value
    stripped = value.strip()
    if not stripped:
        return None
    if field_name == "logo_url" and stripped.startswith("data:image/"):
        if not any(stripped.startswith(prefix) for prefix in ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")):
            raise ValueError("Logo data URL must be PNG, JPEG, or WebP.")
        if len(stripped) > 3_000_000:
            raise ValueError("Logo data URL is too large.")
        return stripped
    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be a valid http(s) URL.")
    return stripped


class LocalizedSettings(BaseModel):
    country_code: str = "CI"
    default_currency: str = "FCFA"
    currency_code: str = "XOF"
    primary_language: str = "fr"
    timezone: str = "Africa/Abidjan"
    date_format: str = "dd/MM/yyyy"
    time_format: str = "HH:mm"


class SchoolBase(BaseModel):
    name: str
    domain_prefix: str
    school_type: SchoolType = SchoolType.GENERAL
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    registration_number: Optional[str] = None
    country_code: Optional[str] = "CI"
    default_currency: Optional[str] = None
    currency_code: Optional[str] = None
    primary_language: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    address_structured: Optional[InternationalAddress] = None
    phone_country_code: Optional[str] = None

class SchoolCreate(SchoolBase):
    @field_validator("website", "logo_url")
    @classmethod
    def validate_school_urls(cls, value: Optional[str], info):
        return _validate_http_url(value, info.field_name)

class SchoolResponse(SchoolBase):
    id: int
    organization_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    formatted_address: Optional[str] = None
    phone_e164: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    registration_number: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole

class UserCreate(UserBase):
    password: str
    school_domain_prefix: Optional[str] = None # For joining an existing school

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool = False
    is_system_account: bool = False
    school_id: Optional[int]
    account_type: str = "school_user"
    dashboard_path: str = "/dashboard"
    recruiter_payment_status: Optional[str] = None
    is_external_student: bool = False
    numref: Optional[str] = None
    school: Optional[SchoolResponse] = None
    mfa_enabled: bool = False
    phone_number: Optional[str] = None
    profile_photo_url: Optional[str] = None
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class SchoolSettingsUpdate(BaseModel):
    name: Optional[str] = None
    school_type: Optional[SchoolType] = None
    country_code: Optional[str] = None
    default_currency: Optional[str] = None
    currency_code: Optional[str] = None
    primary_language: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    registration_number: Optional[str] = None
    address_structured: Optional[InternationalAddress] = None

    @field_validator("website", "logo_url")
    @classmethod
    def validate_settings_urls(cls, value: Optional[str], info):
        return _validate_http_url(value, info.field_name)


class SchoolSettingsResponse(SchoolResponse):
    localization_profile: dict = Field(default_factory=dict)
    school_type_profile: dict = Field(default_factory=dict)


class AIProviderBase(BaseModel):
    name: str
    provider_type: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    account_label: Optional[str] = None
    available_credits: int = Field(default=0, ge=0)
    is_active: bool = False
    priority: int = 100
    cost_per_1k_input_tokens: float = 0
    cost_per_1k_output_tokens: float = 0
    currency: str = "USD"


class AIProviderCreate(AIProviderBase):
    pass


class AIProviderUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    account_label: Optional[str] = None
    available_credits: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None
    currency: Optional[str] = None


class AIProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    account_label: Optional[str] = None
    available_credits: int = 0
    credits_last_synced_at: Optional[datetime] = None
    is_active: bool
    priority: int
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    currency: str
    has_api_key: bool = False
    balance_api_supported: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlatformAISettingsUpdate(BaseModel):
    low_credit_threshold: int = Field(ge=0)
    notification_enabled: bool = True


class PlatformAIMonitoringResponse(BaseModel):
    providers: List[AIProviderResponse] = []
    total_provider_credits: int = 0
    total_credits_purchased: int = 0
    total_wallet_balance: int = 0
    remaining_system_credits: int = 0
    low_credit_threshold: int = 0
    notification_enabled: bool = True
    low_credit_alert: bool = False


class AICreditPackBase(BaseModel):
    name: str
    description: Optional[str] = None
    credits_amount: int = Field(gt=0)
    price: float = Field(ge=0)
    currency: str = "FCFA"
    country_code: str = "CI"
    region: str = "africa"
    target_type: str = Field(default="both", pattern="^(user|school|both)$")
    is_active: bool = True
    validity_days: Optional[int] = None


class AICreditPackCreate(AICreditPackBase):
    pass


class AICreditPackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    credits_amount: Optional[int] = Field(default=None, gt=0)
    price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    target_type: Optional[str] = Field(default=None, pattern="^(user|school|both)$")
    is_active: Optional[bool] = None
    validity_days: Optional[int] = None


class AICreditPackResponse(AICreditPackBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AIWalletResponse(BaseModel):
    id: int
    owner_type: str
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    balance_credits: int
    total_purchased_credits: int
    total_used_credits: int
    daily_credit_limit: Optional[int] = None
    monthly_credit_limit: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AIWalletLimitUpdate(BaseModel):
    daily_credit_limit: Optional[int] = Field(default=None, ge=0)
    monthly_credit_limit: Optional[int] = Field(default=None, ge=0)


class AIWalletAccessUpdate(BaseModel):
    is_active: bool


class AICreditAdjustmentRequest(BaseModel):
    owner_type: str = Field(pattern="^(user|school)$")
    credits_amount: int
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    transaction_type: str = "admin_adjustment"
    description: Optional[str] = None


class AIUsageLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    provider_id: Optional[int] = None
    model_name: Optional[str] = None
    module_name: Optional[str] = None
    action_type: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    credits_charged: int
    estimated_cost: float
    currency: str
    request_summary: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AICreditTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    transaction_type: str
    credits_amount: int
    balance_before: int
    balance_after: int
    payment_id: Optional[int] = None
    usage_log_id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AICreditPurchaseRequest(BaseModel):
    pack_id: int
    owner_type: str = "user"
    target_user_id: Optional[int] = None
    provider: str = Field(default="cash", pattern="^(cash|free|stripe|djamo|cinetpay)$")
    payment_method: Optional[str] = None
    mobile_money_network: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    note: Optional[str] = None


class PlatformPaymentCreate(BaseModel):
    payment_type: str = "ai_credit_purchase"
    pack_id: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    provider: str = "manual"
    provider_reference: Optional[str] = None
    beneficiary_entity: Optional[str] = None
    credits_amount: int = 0
    owner_type: str = "user"
    target_user_id: Optional[int] = None
    mobile_money_network: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class PlatformPaymentWebhook(BaseModel):
    reference: str
    status: str
    provider_reference: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class PlatformPaymentResponse(BaseModel):
    id: int
    reference: str
    payer_user_id: Optional[int] = None
    school_id: Optional[int] = None
    payment_type: str
    amount: float
    currency: str
    country_code: Optional[str] = None
    region: Optional[str] = None
    provider: str
    provider_reference: Optional[str] = None
    status: str
    beneficiary_entity: str
    pack_id: Optional[int] = None
    credits_amount: int
    wallet_id: Optional[int] = None
    validated_by_id: Optional[int] = None
    validated_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None
    checkout_url: Optional[str] = None
    provider_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ManualAICreditPaymentRequest(BaseModel):
    owner_type: str = Field(pattern="^(user|school)$")
    pack_id: int
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    payment_method: str = Field(pattern="^(cash|free)$")
    internal_reference: Optional[str] = None
    note: Optional[str] = None


class SchoolAICreditAllocationCreate(BaseModel):
    user_id: int
    credits_amount: int = Field(gt=0)
    note: Optional[str] = None


class SchoolAICreditAllocationResponse(BaseModel):
    id: int
    school_id: int
    user_id: int
    school_wallet_id: int
    user_wallet_id: int
    allocated_credits: int
    remaining_credits: int
    consumed_credits: int
    is_active: bool
    granted_by_id: int
    updated_by_id: Optional[int] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SchoolPaymentAccountCreate(BaseModel):
    provider: str
    account_name: str
    merchant_id: Optional[str] = None
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    phone_number: Optional[str] = None
    country_code: str = "CI"
    is_active: bool = True


class SchoolPaymentAccountResponse(BaseModel):
    id: int
    school_id: int
    provider: str
    account_name: str
    merchant_id: Optional[str] = None
    phone_number: Optional[str] = None
    country_code: str
    is_active: bool
    has_api_key: bool = False
    has_secret_key: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SchoolPaymentCreate(BaseModel):
    student_id: Optional[int] = None
    invoice_id: Optional[int] = None
    payment_type: str = "tuition"
    amount: float = Field(gt=0)
    currency: str = "FCFA"
    provider: str = "manual"
    provider_reference: Optional[str] = None
    school_beneficiary_account_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None


class SchoolPaymentWebhook(BaseModel):
    reference: str
    status: str
    provider_reference: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class SchoolPaymentResponse(BaseModel):
    id: int
    reference: str
    school_id: int
    payer_user_id: Optional[int] = None
    student_id: Optional[int] = None
    invoice_id: Optional[int] = None
    payment_type: str
    amount: float
    currency: str
    provider: str
    provider_reference: Optional[str] = None
    school_beneficiary_account_id: Optional[int] = None
    status: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceResponse(BaseModel):
    theme: str = "light"
    help_open_mode: str = "page"
    email_notifications_enabled: bool = True
    language: Optional[str] = None
    active_organization_id: Optional[int] = None
    active_school_id: Optional[int] = None
    active_school_model_assignment_id: Optional[int] = None
    active_academic_year_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceUpdate(BaseModel):
    theme: Optional[str] = Field(default=None, pattern="^(light|dark|system)$")
    help_open_mode: Optional[str] = Field(default=None, pattern="^(page|modal|drawer)$")
    email_notifications_enabled: Optional[bool] = None
    language: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class SchoolContextUpdate(BaseModel):
    school_model_assignment_id: int
    academic_year_id: Optional[int] = None


class SchoolModelAssignmentCreate(BaseModel):
    school_id: int
    model_codes: List[str]
    seed_defaults: bool = True

    model_config = ConfigDict(protected_namespaces=())


class SchoolModelAssignmentUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    ai_enabled: Optional[bool] = None
    monthly_ai_credit_limit: Optional[int] = Field(default=None, ge=0)


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    country: str = "CI"
    currency: str = "XOF"
    timezone: str = "Africa/Abidjan"


class OrganizationSchoolCreate(BaseModel):
    organization_id: int
    school: SchoolCreate
    model_codes: List[str]
    seed_defaults: bool = True

    model_config = ConfigDict(protected_namespaces=())


class CartItemCreate(BaseModel):
    item_type: str
    title: str
    description: Optional[str] = None
    quantity: int = Field(default=1, gt=0)
    unit_amount: float = Field(gt=0)
    currency: str = "FCFA"
    provider_scope: str = Field(default="school", pattern="^(school|platform)$")
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: int
    item_type: str
    title: str
    description: Optional[str] = None
    quantity: int
    unit_amount: float
    currency: str
    provider_scope: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    line_total: float = 0

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    subtotal: float
    total: float
    currency: str


class CheckoutRequest(BaseModel):
    provider: str = Field(pattern="^(stripe|djamo|cinetpay|manual)$")
    mobile_money_network: Optional[str] = Field(default=None, pattern="^(orange_money|wave|mtn_money|moov_money)$")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    platform_payments: List[PlatformPaymentResponse] = []
    school_payments: List[SchoolPaymentResponse] = []
    checkout_url: Optional[str] = None
    status: str


class NotificationHistoryResponse(BaseModel):
    id: int
    event_type: str
    channel: str
    subject: Optional[str] = None
    message: str
    status: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionSettingsUpdate(BaseModel):
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    storage_quota_mb: Optional[int] = None
    current_billing_period_end: Optional[datetime] = None


class SchoolSubscriptionChange(BaseModel):
    plan: str = Field(pattern="^(free|pro|max)$")
    billing_cycle: str = Field(default="monthly", pattern="^(monthly|yearly)$")
    payment_provider: Optional[str] = Field(default=None, pattern="^(cash|stripe|djamo|cinetpay|manual)$")


class SchoolSubscriptionResponse(BaseModel):
    id: int
    school_id: int
    plan: str
    billing_cycle: str
    amount: float
    currency: str
    status: str
    started_at: Optional[datetime] = None
    next_renewal_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    payment_provider: Optional[str] = None
    payment_reference: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role: UserRole
    is_active: Optional[bool] = None


class RolePermissionUpdate(BaseModel):
    permissions: List[str]
    role: Optional[UserRole] = None


class RolePermissionResponse(BaseModel):
    role: UserRole
    base_permissions: List[str]
    enabled_permissions: List[str]
    disabled_permissions: List[str] = []
    available_permissions: List[str]
    school_id: Optional[int] = None

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None
    token_version: Optional[int] = None


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaVerifyRequest(BaseModel):
    code: str


class MfaStatusResponse(BaseModel):
    enabled: bool

# Student Schemas
class StudentProfileBase(BaseModel):
    registration_number: str
    date_of_birth: datetime
    gender: str
    student_address: Optional[str] = None
    student_address_structured: Optional[InternationalAddress] = None
    parent_name: str
    parent_phone: str
    parent_phone_country_code: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    parent_address: Optional[str] = None
    parent_address_structured: Optional[InternationalAddress] = None
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
    school_id: Optional[int] = None
    transfer_reason: Optional[str] = None
    profile: StudentProfileBase

class StudentUpdateProfile(BaseModel):
    registration_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    student_address: Optional[str] = None
    student_address_structured: Optional[InternationalAddress] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_phone_country_code: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    parent_address: Optional[str] = None
    parent_address_structured: Optional[InternationalAddress] = None
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
    # Tolerant on read: admission/import-created profiles may lack these until
    # completed, and a stored malformed parent email must not 500 the roster.
    # Creation schemas keep these required/validated.
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    parent_email: Optional[str] = None
    student_formatted_address: Optional[str] = None
    parent_phone_e164: Optional[str] = None
    parent_formatted_address: Optional[str] = None
    education_history: List[EducationHistoryResponse] = []
    model_config = ConfigDict(from_attributes=True)

class StudentResponse(UserResponse):
    student_profile: Optional[StudentProfileResponse] = None


class StudentEnrollmentCreate(BaseModel):
    student_global_profile_id: Optional[int] = None
    student_user_id: Optional[int] = None
    school_model_assignment_id: Optional[int] = None
    academic_year_id: Optional[int] = None
    class_id: Optional[int] = None
    level_id: Optional[int] = None
    program_id: Optional[int] = None
    enrollment_type: str = "full_time"
    schedule_type: str = "morning"
    allows_concurrent_enrollment: bool = False
    primary_enrollment: bool = True
    module_id: Optional[int] = None
    training_program_id: Optional[int] = None
    certification_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: List[str] = []
    location: Optional[str] = None
    force: bool = False
    override_reason: Optional[str] = None


class StudentTransferCreate(BaseModel):
    student_global_profile_id: int
    from_enrollment_id: int
    to_school_model_assignment_id: int
    to_academic_year_id: int
    academic_data_access_level: str = "full_history"
    notes: Optional[str] = None


class StudentTransferDecision(BaseModel):
    decision: str
    notes: Optional[str] = None
    class_id: Optional[int] = None
    program_id: Optional[int] = None
    enrollment_type: str = "full_time"
    schedule_type: str = "morning"


class AcademicYearCloseRequest(BaseModel):
    school_model_assignment_id: Optional[int] = None
    confirmation: str


class HistoricalEditGrantCreate(BaseModel):
    organization_id: int
    school_id: int
    academic_year_id: int
    student_global_profile_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    reason: str = Field(min_length=5)
    valid_until: datetime


class StudentImportCommit(BaseModel):
    batch_id: int
    confirm: bool = False


class StudentImportRowsPreview(BaseModel):
    rows: List[Dict[str, Any]]
    filename: str = "import.json"


class StudentCVUpdate(BaseModel):
    professional_title: Optional[str] = None
    summary: Optional[str] = None
    sectors: List[str] = []
    looking_for_job: Optional[bool] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    academic_timeline: Optional[List[Dict[str, Any]]] = None
    academic_credentials: List[Dict[str, Any]] = []
    certificates: List[Dict[str, Any]] = []
    skills: List[str] = []
    detailed_skills: List[Dict[str, Any]] = []
    languages: List[str] = []
    portfolio: List[Dict[str, Any]] = []
    availability: Optional[str] = None
    cv_photo_url: Optional[str] = None
    desired_location: Optional[str] = None


class StudentCVWorkHistoryCreate(BaseModel):
    company: str
    sector: Optional[str] = None
    position: str
    experience_type: str = "stage"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    current: bool = False
    description: Optional[str] = None
    missions: List[str] = []
    skills_used: List[str] = []
    technologies_used: List[str] = []
    skills_acquired: List[str] = []
    proof_document_url: Optional[str] = None
    reference_contact: Optional[str] = None


class StudentCVWorkHistoryResponse(StudentCVWorkHistoryCreate):
    id: int
    locked: bool = False
    verified_by_entity: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentCVResponse(BaseModel):
    id: int
    sharecode: str
    share_enabled: bool
    is_external: bool
    professional_title: Optional[str] = None
    summary: Optional[str] = None
    sectors: List[str] = []
    looking_for_job: bool
    cv_photo_url: Optional[str] = None
    privacy_settings: Dict[str, Any] = {}
    academic_timeline: List[Dict[str, Any]] = []
    academic_credentials: List[Dict[str, Any]] = []
    certificates: List[Dict[str, Any]] = []
    skills: List[str] = []
    detailed_skills: List[Dict[str, Any]] = []
    languages: List[str] = []
    portfolio: List[Dict[str, Any]] = []
    availability: Optional[str] = None
    desired_location: Optional[str] = None
    total_experience_years: float = 0
    external_identity: Optional[Dict[str, Any]] = None
    work_history: List[StudentCVWorkHistoryResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SharecodeLookup(BaseModel):
    sharecode: str = Field(min_length=4, max_length=80)


class ExternalStudentRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    sector: Optional[str] = None
    professional_title: Optional[str] = None
    payment_provider: str = Field(default="manual", pattern="^(cash|free|stripe|djamo|cinetpay|manual)$")


class RecruiterRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    contact_name: str
    sector: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    plan: str = "sharecode_only"
    payment_provider: str = Field(default="manual", pattern="^(cash|free|stripe|djamo|cinetpay|manual)$")


class RecruiterProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    sector: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    company_description: Optional[str] = None


class RecruiterSubscriptionUpdate(BaseModel):
    plan: str = "sharecode_only"
    duration_months: int = Field(default=1, ge=1, le=12)
    auto_renew: bool = False
    payment_provider: str = Field(default="manual", pattern="^(cash|free|stripe|djamo|cinetpay|manual)$")


class EmploymentAICreditPurchase(BaseModel):
    credits: int = Field(ge=10, le=100000)
    payment_provider: str = Field(default="manual", pattern="^(cash|free|stripe|djamo|cinetpay|manual)$")


class EmploymentAgentRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    mode: str = "recruiter"


class JobOfferCreate(BaseModel):
    title: str
    company: str
    sector: str
    offer_type: str = "emploi"
    location: Optional[str] = None
    workplace_mode: str = "on_site"
    description: str
    application_start_at: Optional[datetime] = None
    missions: Optional[List[str]] = []
    required_skills: Optional[List[str]] = []
    desired_skills: Optional[List[str]] = []
    required_languages: Optional[List[str]] = []
    required_degree: Optional[str] = None
    required_level: Optional[str] = None
    required_experience: Optional[str] = None
    salary: Optional[str] = None
    salary_fixed: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "FCFA"
    contract_type: Optional[str] = None
    minimum_academic_level: Optional[str] = None
    required_years_experience: Optional[float] = None
    positions_count: int = 1
    desired_start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str = "draft"


class JobOfferUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    sector: Optional[str] = None
    offer_type: Optional[str] = None
    location: Optional[str] = None
    workplace_mode: Optional[str] = None
    description: Optional[str] = None
    application_start_at: Optional[datetime] = None
    missions: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    desired_skills: Optional[List[str]] = None
    required_languages: Optional[List[str]] = None
    required_degree: Optional[str] = None
    required_level: Optional[str] = None
    required_experience: Optional[str] = None
    salary: Optional[str] = None
    salary_fixed: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    contract_type: Optional[str] = None
    minimum_academic_level: Optional[str] = None
    required_years_experience: Optional[float] = None
    positions_count: Optional[int] = None
    desired_start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None


class JobOfferResponse(JobOfferCreate):
    id: int
    recruiter_id: int
    recruiter_logo_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    ai_match_summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobApplicationCreate(BaseModel):
    motivation_message: Optional[str] = None
    attached_documents: List[Dict[str, Any]] = []


class JobApplicationResponse(BaseModel):
    id: int
    student_cv_id: int
    job_offer_id: int
    motivation_message: Optional[str] = None
    attached_documents: Optional[List[Dict[str, Any]]] = []
    ai_match_score: float = 0
    ai_match_details: Optional[Dict[str, Any]] = None
    status: str
    status_history: Optional[List[Dict[str, Any]]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmploymentNotificationCreate(BaseModel):
    audience: str = Field(pattern="^(all_recruiters|all_students|targeted|ai_campaign)$")
    title: str
    message: str
    recruiter_id: Optional[int] = None
    student_cv_id: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None


class JobInterviewCreate(BaseModel):
    job_application_id: int
    scheduled_at: datetime
    duration_minutes: int = 30
    mode: str = "presentiel"
    location_or_link: Optional[str] = None
    note: Optional[str] = None


class JobInterviewResponse(BaseModel):
    id: int
    recruiter_id: int
    student_cv_id: int
    job_application_id: int
    scheduled_at: datetime
    duration_minutes: int
    mode: str
    location_or_link: Optional[str] = None
    note: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Teacher Schemas
class TeacherProfileBase(BaseModel):
    specialization: Optional[str] = None
    join_date: Optional[datetime] = None
    bio: Optional[str] = None

class TeacherCreate(UserCreate):
    school_id: Optional[int] = None
    transfer_reason: Optional[str] = None
    profile: TeacherProfileBase

class TeacherUpdateProfile(BaseModel):
    specialization: Optional[str] = None
    join_date: Optional[datetime] = None
    bio: Optional[str] = None

class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    phone_country_code: Optional[str] = None
    address: Optional[str] = None
    address_structured: Optional[InternationalAddress] = None
    profile: Optional[TeacherUpdateProfile] = None

class TeacherProfileResponse(TeacherProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TeacherResponse(UserResponse):
    phone_number: Optional[str] = None
    phone_country_code: Optional[str] = None
    phone_e164: Optional[str] = None
    address: Optional[str] = None
    address_structured: Optional[InternationalAddress] = None
    formatted_address: Optional[str] = None
    teacher_profile: Optional[TeacherProfileResponse] = None


class TeacherAssignmentCreate(BaseModel):
    employment_type: str = "full_time"
    specialization: Optional[str] = None


class TeacherAssignmentResponse(BaseModel):
    id: int
    user_id: int
    school_id: int
    school_name: Optional[str] = None
    school_model_assignment_id: Optional[int] = None
    employment_type: str
    specialization: Optional[str] = None
    is_primary: bool
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

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
    school_id: Optional[int] = None

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
    school_id: Optional[int] = None

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
    school_id: Optional[int] = None

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
    duration_minutes: Optional[int] = None
    is_locked: bool = False
    lock_scope: Optional[str] = None
    status: str = "draft"
    generation_batch: Optional[str] = None
    constraints_snapshot: Optional[Dict[str, Any]] = None

class TimetableCreate(TimetableBase):
    pass

class TimetableUpdate(BaseModel):
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room: Optional[str] = None
    class_id: Optional[int] = None
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_locked: Optional[bool] = None
    lock_scope: Optional[str] = None
    status: Optional[str] = None
    constraints_snapshot: Optional[Dict[str, Any]] = None

class TimetableBulkUpdate(BaseModel):
    entry_ids: List[int]
    changes: TimetableUpdate

class TimetableGenerationRequest(BaseModel):
    school_id: Optional[int] = None
    mode: str = "partial"
    scope_type: Optional[str] = None
    scope_id: Optional[int] = None
    level: Optional[str] = None
    subject_ids: List[int] = []
    preserve_locks: bool = True
    constraints: Dict[str, Any] = {}

class TimetablePublishRequest(BaseModel):
    school_id: Optional[int] = None
    class_id: Optional[int] = None
    teacher_id: Optional[int] = None
    level: Optional[str] = None


class SchoolMembershipResponse(BaseModel):
    id: int
    user_id: int
    school_id: int
    role: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool
    membership_status: str
    transfer_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TimetableResponse(TimetableBase):
    id: int
    conflict_status: str = "clear"
    conflict_details: Optional[List[Dict[str, Any]]] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TimetableConstraintRuleBase(BaseModel):
    rule_type: str
    name: Optional[str] = None
    parameters: Dict[str, Any] = {}
    severity: str = "warning"
    is_active: bool = True
    school_model_assignment_id: Optional[int] = None


class TimetableConstraintRuleCreate(TimetableConstraintRuleBase):
    pass


class TimetableConstraintRuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    school_model_assignment_id: Optional[int] = None


class TimetableConstraintRuleResponse(TimetableConstraintRuleBase):
    id: int
    school_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# Facilities (campus / buildings / rooms / equipment)

class CampusCreate(BaseModel):
    name: str
    address: Optional[str] = None
    is_active: bool = True


class CampusResponse(CampusCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class BuildingCreate(BaseModel):
    name: str
    campus_id: Optional[int] = None
    is_active: bool = True


class BuildingResponse(BuildingCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class RoomEquipmentItem(BaseModel):
    id: Optional[int] = None
    name: str
    quantity: int = 1
    model_config = ConfigDict(from_attributes=True)


class RoomCreate(BaseModel):
    name: str
    building_id: Optional[int] = None
    room_type: str = "classroom"
    capacity: Optional[int] = None
    is_active: bool = True
    equipment: List[RoomEquipmentItem] = []


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    building_id: Optional[int] = None
    room_type: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    equipment: Optional[List[RoomEquipmentItem]] = None


class RoomResponse(BaseModel):
    id: int
    school_id: int
    building_id: Optional[int] = None
    name: str
    room_type: str
    capacity: Optional[int] = None
    is_active: bool
    equipment: List[RoomEquipmentItem] = []
    model_config = ConfigDict(from_attributes=True)


# Timetable grid configuration

class TimetableSlot(BaseModel):
    start: str
    end: str
    kind: str = "course"  # course | break | lunch


class TimetableConfigUpsert(BaseModel):
    working_days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    slots: List[TimetableSlot] = []
    school_model_assignment_id: Optional[int] = None
    is_active: bool = True


class TimetableConfigResponse(BaseModel):
    id: int
    school_id: int
    school_model_assignment_id: Optional[int] = None
    working_days: List[str] = []
    slots: List[Dict[str, Any]] = []
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class SchoolHolidayCreate(BaseModel):
    date: datetime
    name: Optional[str] = None


class SchoolHolidayResponse(SchoolHolidayCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class SubjectRequirementCreate(BaseModel):
    subject_id: int
    class_id: Optional[int] = None
    level: Optional[str] = None
    weekly_sessions: int = 1
    school_model_assignment_id: Optional[int] = None


class SubjectRequirementResponse(SubjectRequirementCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class TimetableOptimizeRequest(BaseModel):
    candidate_count: int = 3


class TimetableOptimizeCommit(BaseModel):
    seed: int
    candidate_count: int = 3
    preserve_locks: bool = True


class TimetableSimulateRequest(BaseModel):
    scenario: str  # teacher_absent | extra_working_day
    params: Dict[str, Any] = {}


class TeacherAbsenceCreate(BaseModel):
    teacher_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    reason: Optional[str] = None


class TeacherAbsenceResponse(TeacherAbsenceCreate):
    id: int
    school_id: int
    status: str
    model_config = ConfigDict(from_attributes=True)


class SubstitutionApply(BaseModel):
    timetable_id: int
    substitute_teacher_id: int

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
    payment_method: str = Field(default="cash", pattern="^(cash|stripe|djamo|cinetpay|mobile_money|bank_transfer|free)$")
    internal_reference: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    amount: float
    payment_date: datetime
    note: Optional[str] = None
    payment_method: str = "cash"
    status: str = "successful"
    internal_reference: Optional[str] = None
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


class PartnerCompanyBase(BaseModel):
    name: str
    rccm_number: Optional[str] = None
    tax_number: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hr_manager_name: Optional[str] = None
    hr_manager_role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    max_simultaneous_interns: Optional[int] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    partnership_file_id: Optional[int] = None
    status: str = "active"


class PartnerCompanyCreate(PartnerCompanyBase):
    pass


class PartnerCompanyUpdate(BaseModel):
    name: Optional[str] = None
    rccm_number: Optional[str] = None
    tax_number: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hr_manager_name: Optional[str] = None
    hr_manager_role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    max_simultaneous_interns: Optional[int] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    partnership_file_id: Optional[int] = None
    status: Optional[str] = None


class PartnerCompanyResponse(PartnerCompanyBase):
    id: int
    interns_count: int = 0
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InternshipCreate(BaseModel):
    student_id: Optional[int] = None
    student_ids: List[int] = Field(default_factory=list)
    company_id: Optional[int] = None
    company_name: str
    academic_level: Optional[str] = None
    class_id: Optional[int] = None
    program: Optional[str] = None
    training_program: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    objectives: Optional[str] = None
    service_department: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_role: Optional[str] = None
    supervisor_phone: Optional[str] = None
    supervisor_email: Optional[EmailStr] = None
    teacher_ref_id: Optional[int] = None
    pedagogy_coordinator_id: Optional[int] = None
    internship_manager_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    weeks_count: Optional[int] = None
    expected_schedule: Optional[str] = None
    status: str = "planned"
    notes: Optional[str] = None


class InternshipUpdate(BaseModel):
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    academic_level: Optional[str] = None
    class_id: Optional[int] = None
    program: Optional[str] = None
    training_program: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    objectives: Optional[str] = None
    service_department: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_role: Optional[str] = None
    supervisor_phone: Optional[str] = None
    supervisor_email: Optional[EmailStr] = None
    teacher_ref_id: Optional[int] = None
    pedagogy_coordinator_id: Optional[int] = None
    internship_manager_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    weeks_count: Optional[int] = None
    expected_schedule: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    ai_summary: Optional[str] = None
    final_score: Optional[float] = None


class InternshipResponse(InternshipCreate):
    id: int
    company_id: Optional[int] = None
    assignments_count: int = 0
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InternshipAssignmentResponse(BaseModel):
    id: int
    internship_id: int
    student_id: int
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    status: str
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InternshipFollowUpCreate(BaseModel):
    internship_id: int
    student_id: Optional[int] = None
    date: datetime
    presence_status: str = "present"
    activities: Optional[str] = None
    tasks_description: Optional[str] = None
    developed_skills: Optional[str] = None
    tools_used: Optional[str] = None
    difficulties: Optional[str] = None
    supervisor_observation: Optional[str] = None


class InternshipFollowUpResponse(InternshipFollowUpCreate):
    id: int
    supervisor_user_id: Optional[int] = None
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InternshipLogbookCreate(BaseModel):
    internship_id: int
    student_id: int
    date: datetime
    tasks_done: Optional[str] = None
    acquired_skills: Optional[str] = None
    difficulties: Optional[str] = None
    proposed_solutions: Optional[str] = None
    hours_count: Optional[float] = None


class InternshipLogbookUpdate(BaseModel):
    validation_status: str
    supervisor_comment: Optional[str] = None


class InternshipLogbookResponse(InternshipLogbookCreate):
    id: int
    validation_status: str
    supervisor_comment: Optional[str] = None
    validated_by_id: Optional[int] = None
    school_id: int
    created_at: datetime
    validated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InternshipEvaluationCreate(BaseModel):
    internship_id: int
    student_id: Optional[int] = None
    evaluation_type: str = "company"
    scores: Dict[str, Any] = Field(default_factory=dict)
    company_score: Optional[float] = None
    report_score: Optional[float] = None
    defense_score: Optional[float] = None
    practical_score: Optional[float] = None
    final_score: Optional[float] = None
    comments: Optional[str] = None


class InternshipEvaluationResponse(InternshipEvaluationCreate):
    id: int
    evaluator_id: Optional[int] = None
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InternshipDocumentCreate(BaseModel):
    internship_id: int
    student_id: Optional[int] = None
    document_type: str
    title: str
    secure_file_id: Optional[int] = None
    status: str = "available"


class InternshipDocumentResponse(InternshipDocumentCreate):
    id: int
    school_id: int
    uploaded_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InternshipDashboardResponse(BaseModel):
    total_internships: int
    active_internships: int
    completed_internships: int
    partner_companies: int
    students_in_internship: int
    validation_rate: float
    insertion_rate: float
    by_company: Dict[str, int]
    by_level: Dict[str, int]
    by_country: Dict[str, int]


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


class AdmissionEnrollmentCreate(BaseModel):
    email: str
    password: str = "ChangeMe123!Secure"
    full_name: Optional[str] = None
    registration_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    class_id: Optional[int] = None
    generate_fees: bool = True
    create_registration_documents: bool = True


class AdmissionEnrollmentResponse(BaseModel):
    application_id: int
    student_user_id: int
    student_profile_id: int
    class_id: Optional[int] = None
    generated_fees: int
    registration_documents: int


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
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    capacity: Optional[int] = None
    is_active: bool = True


class TransportRouteResponse(TransportRouteCreate):
    id: int
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransportDriverCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[datetime] = None
    employment_status: str = "active"
    medical_clearance: bool = False
    notes: Optional[str] = None
    is_active: bool = True


class TransportDriverUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[datetime] = None
    employment_status: Optional[str] = None
    medical_clearance: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TransportDriverResponse(TransportDriverCreate):
    id: int
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransportVehicleCreate(BaseModel):
    name: str
    vehicle_type: str = "bus"
    registration: Optional[str] = None
    vin: Optional[str] = None
    capacity: int = 0
    insurance_expiry: Optional[datetime] = None
    mileage: float = 0
    status: str = "operational"
    notes: Optional[str] = None
    is_active: bool = True


class TransportVehicleUpdate(BaseModel):
    name: Optional[str] = None
    vehicle_type: Optional[str] = None
    registration: Optional[str] = None
    vin: Optional[str] = None
    capacity: Optional[int] = None
    insurance_expiry: Optional[datetime] = None
    mileage: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TransportVehicleResponse(TransportVehicleCreate):
    id: int
    school_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransportStopCreate(BaseModel):
    route_id: int
    name: str
    sequence: int = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_m: int = 100
    scheduled_arrival: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class TransportStopUpdate(BaseModel):
    name: Optional[str] = None
    sequence: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_m: Optional[int] = None
    scheduled_arrival: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class TransportStopResponse(TransportStopCreate):
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


class CourseEnrollmentCreate(BaseModel):
    student_id: int
    course_unit_id: int
    semester_id: Optional[int] = None
    status: str = "registered"
    score: Optional[float] = None
    grade: Optional[str] = None
    grade_point: Optional[float] = None
    credits_attempted: Optional[float] = None
    credits_validated: Optional[float] = None


class CourseEnrollmentResponse(CourseEnrollmentCreate):
    id: int
    school_id: int
    registered_by_id: Optional[int] = None
    registered_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LmdSummaryResponse(BaseModel):
    student_id: int
    credits_attempted: float
    credits_validated: float
    gpa: Optional[float] = None
    completion_rate: float
    enrollments: List[CourseEnrollmentResponse]


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


class JournalLineCreate(BaseModel):
    account_id: int
    label: Optional[str] = None
    debit: float = 0
    credit: float = 0


class JournalEntryCreate(BaseModel):
    entry_date: datetime
    reference: Optional[str] = None
    description: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    lines: List[JournalLineCreate]


class JournalLineResponse(JournalLineCreate):
    id: int
    school_id: int
    model_config = ConfigDict(from_attributes=True)


class JournalEntryResponse(JournalEntryCreate):
    id: int
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    lines: List[JournalLineResponse] = []
    model_config = ConfigDict(from_attributes=True)


class BankReconciliationCreate(BaseModel):
    bank_transaction_id: int
    journal_entry_id: Optional[int] = None
    matched_amount: float
    status: str = "matched"
    notes: Optional[str] = None


class BankReconciliationResponse(BankReconciliationCreate):
    id: int
    school_id: int
    reconciled_by_id: Optional[int] = None
    reconciled_at: datetime
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
    template_key: Optional[str] = None
    locale: str = "fr"


class NotificationMessageResponse(NotificationMessageCreate):
    id: int
    status: NotificationStatus
    provider_response: Optional[str] = None
    attempts: int = 0
    next_retry_at: Optional[datetime] = None
    school_id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    school_id: Optional[int] = None
    actor_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SecurityEventResponse(BaseModel):
    id: int
    event_type: str
    severity: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    school_id: Optional[int] = None
    actor_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SecureFileResponse(BaseModel):
    id: int
    original_filename: str
    display_name: Optional[str] = None
    category: Optional[str] = None
    content_type: str
    file_extension: Optional[str] = None
    size_bytes: int
    checksum_sha256: str
    storage_backend: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    status: str
    visibility: str = "private"
    is_shareable: bool = False
    approval_status: str = "approved"
    expires_at: Optional[datetime] = None
    download_limit: Optional[int] = None
    access_count: int = 0
    scan_status: str
    scan_details: Optional[str] = None
    school_id: Optional[int] = None
    uploaded_by_id: Optional[int] = None
    created_at: datetime
    deleted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class DocumentRecipientResponse(BaseModel):
    id: int
    type: str
    name: str
    role: Optional[str] = None
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    numref: Optional[str] = None
    subtitle: Optional[str] = None


class DocumentShareCreate(BaseModel):
    file_id: int
    share_type: str
    mode: str = "private"
    can_reshare: bool = False
    recipient_user_ids: List[int] = []
    recipient_school_ids: List[int] = []
    recipient_numrefs: List[str] = []
    expires_at: Optional[datetime] = None
    download_limit: Optional[int] = None


class DocumentShareResponse(BaseModel):
    id: int
    file_id: int
    share_type: str
    mode: str
    can_reshare: bool
    recipient_user_id: Optional[int] = None
    recipient_school_id: Optional[int] = None
    recipient_numref: Optional[str] = None
    status: str
    expires_at: Optional[datetime] = None
    download_limit: Optional[int] = None
    download_count: int
    created_by_id: int
    school_id: Optional[int] = None
    created_at: datetime
    revoked_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ComplianceExportResponse(BaseModel):
    generated_at: datetime
    school_id: Optional[int] = None
    user_id: Optional[int] = None
    payload: dict


class ComplianceEraseRequest(BaseModel):
    user_id: int
    reason: str
    anonymize_only: bool = True


class DataConsentCreate(BaseModel):
    subject_user_id: int
    consent_type: str
    granted: bool = True
    source: Optional[str] = None
    locale: str = "fr"
    policy_version: Optional[str] = None


class DataConsentResponse(DataConsentCreate):
    id: int
    school_id: Optional[int] = None
    recorded_by_id: Optional[int] = None
    recorded_at: datetime
    revoked_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class DataRetentionRuleCreate(BaseModel):
    data_category: str
    retention_days: int
    legal_basis: Optional[str] = None
    action: str = "review"


class DataRetentionRuleResponse(DataRetentionRuleCreate):
    id: int
    school_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class StartupWizardRequest(BaseModel):
    academic_year_name: str
    start_date: datetime
    end_date: datetime
    template: Optional[str] = None
    create_defaults: bool = True
