"""Initial frozen base schema.

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

revision = "20260601_0001"
down_revision = None
branch_labels = None
depends_on = None

BASE_METADATA = sa.MetaData()

administrativerequeststatus_enum = sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'DONE', name='administrativerequeststatus')
administrativerequesttype_enum = sa.Enum('REPORT_CARD', 'CERTIFICATE', 'ABSENCE_AUTHORIZATION', 'OTHER', name='administrativerequesttype')
admissionstatus_enum = sa.Enum('DRAFT', 'SUBMITTED', 'ACCEPTED', 'REJECTED', 'ENROLLED', name='admissionstatus')
approvalstatus_enum = sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', name='approvalstatus')
assessmenttype_enum = sa.Enum('EXAM', 'HOMEWORK', 'QUIZ', 'PROJECT', 'PARTICIPATION', name='assessmenttype')
assignmentstatus_enum = sa.Enum('DRAFT', 'PUBLISHED', 'CLOSED', name='assignmentstatus')
attendancestatus_enum = sa.Enum('PRESENT', 'ABSENT', 'LATE', 'EXCUSED', name='attendancestatus')
cashclosurestatus_enum = sa.Enum('DRAFT', 'SUBMITTED', 'APPROVED', name='cashclosurestatus')
certificatestatus_enum = sa.Enum('GENERATED', 'BLOCKED', name='certificatestatus')
certificatetype_enum = sa.Enum('SCHOOLING', 'ENROLLMENT', 'ABSENCE_AUTHORIZATION', 'PAYMENT', name='certificatetype')
dayofweek_enum = sa.Enum('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY', name='dayofweek')
expensecategory_enum = sa.Enum('SALARIES', 'UTILITIES', 'MAINTENANCE', 'SUPPLIES', 'EQUIPMENT', 'OTHER', name='expensecategory')
feestatus_enum = sa.Enum('PENDING', 'PARTIAL', 'PAID', 'OVERDUE', name='feestatus')
inventorystatus_enum = sa.Enum('AVAILABLE', 'LOW_STOCK', 'OUT_OF_STOCK', name='inventorystatus')
invoicestatus_enum = sa.Enum('DRAFT', 'APPROVED', 'PAID', 'CANCELLED', name='invoicestatus')
leavestatus_enum = sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='leavestatus')
loanstatus_enum = sa.Enum('ACTIVE', 'RETURNED', 'OVERDUE', name='loanstatus')
notificationchannel_enum = sa.Enum('SMS', 'EMAIL', 'WHATSAPP', name='notificationchannel')
notificationstatus_enum = sa.Enum('QUEUED', 'SENT', 'FAILED', name='notificationstatus')
payrollstatus_enum = sa.Enum('DRAFT', 'APPROVED', 'PAID', name='payrollstatus')
schooltype_enum = sa.Enum('PRIMARY', 'SECONDARY', 'GENERAL', 'TECHNICAL', 'VOCATIONAL', 'PROFESSIONAL', 'UNIVERSITY', name='schooltype')
studentstatus_enum = sa.Enum('ASSIGNED', 'UNASSIGNED', name='studentstatus')
submissionstatus_enum = sa.Enum('SUBMITTED', 'GRADED', name='submissionstatus')
userrole_enum = sa.Enum('SUPER_ADMIN', 'SCHOOL_ADMIN', 'CASHIER', 'REGISTRAR', 'DIRECTION', 'TEACHER', 'STUDENT', 'PARENT', 'STAFF', name='userrole')
sa.Table(
    'schools',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('domain_prefix', sa.String(), index=True, unique=True, nullable=False),
    sa.Column('school_type', schooltype_enum),
    sa.Column('address', sa.String()),
    sa.Column('phone', sa.String()),
    sa.Column('email', sa.String()),
    sa.Column('website', sa.String()),
    sa.Column('logo_url', sa.String()),
    sa.Column('subscription_plan', sa.String()),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'academic_programs',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('sector', sa.String(), index=True, nullable=False),
    sa.Column('level', sa.String(), index=True),
    sa.Column('diploma', sa.String()),
    sa.Column('duration_years', sa.Integer()),
    sa.Column('description', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'academic_years',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('start_date', sa.DateTime(timezone=False)),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('is_current', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
)

sa.Table(
    'books',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('title', sa.String(), index=True, nullable=False),
    sa.Column('author', sa.String(), index=True, nullable=False),
    sa.Column('isbn', sa.String(), index=True, unique=True),
    sa.Column('category', sa.String(), index=True),
    sa.Column('quantity', sa.Integer()),
    sa.Column('available_quantity', sa.Integer()),
    sa.Column('location', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'canteen_meal_plans',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('day_of_week', sa.String()),
    sa.Column('meal_type', sa.String(), nullable=False),
    sa.Column('menu', sa.String()),
    sa.Column('price', sa.Float()),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'chart_accounts',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('code', sa.String(), index=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('account_type', sa.String(), nullable=False),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'expenses',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('title', sa.String(), index=True, nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('category', expensecategory_enum, nullable=False),
    sa.Column('date', sa.DateTime(timezone=False)),
    sa.Column('description', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'inventory_items',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('category', sa.String(), index=True, nullable=False),
    sa.Column('quantity', sa.Integer()),
    sa.Column('minimum_quantity', sa.Integer()),
    sa.Column('location', sa.String()),
    sa.Column('status', inventorystatus_enum, nullable=False),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'notification_providers',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('channel', notificationchannel_enum, nullable=False),
    sa.Column('provider_name', sa.String(), nullable=False),
    sa.Column('api_key_secret', sa.String()),
    sa.Column('sender_id', sa.String()),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'reference_data',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('category', sa.String(), index=True, nullable=False),
    sa.Column('key', sa.String(), index=True, nullable=False),
    sa.Column('value', sa.JSON(), nullable=False),
    sa.Column('order', sa.Integer()),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
)

sa.Table(
    'subjects',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('code', sa.String(), index=True),
    sa.Column('description', sa.String()),
    sa.Column('coefficient', sa.Integer()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
)

sa.Table(
    'transport_routes',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('vehicle_identifier', sa.String()),
    sa.Column('driver_name', sa.String()),
    sa.Column('driver_phone', sa.String()),
    sa.Column('stops', sa.JSON()),
    sa.Column('monthly_fee', sa.Float()),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'users',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('email', sa.String(), index=True, unique=True, nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), index=True),
    sa.Column('role', userrole_enum, nullable=False),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
    sa.Column('phone_number', sa.String()),
    sa.Column('address', sa.String()),
)

sa.Table(
    'admission_applications',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('applicant_name', sa.String(), index=True, nullable=False),
    sa.Column('applicant_phone', sa.String()),
    sa.Column('applicant_email', sa.String()),
    sa.Column('desired_level', sa.String()),
    sa.Column('desired_program_id', sa.Integer(), sa.ForeignKey('academic_programs.id')),
    sa.Column('status', admissionstatus_enum, nullable=False),
    sa.Column('notes', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('handled_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'approval_workflows',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('entity_type', sa.String(), index=True, nullable=False),
    sa.Column('entity_id', sa.Integer(), index=True, nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('requested_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('current_step', sa.Integer()),
    sa.Column('status', approvalstatus_enum, nullable=False),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('decided_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'bank_transactions',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('transaction_date', sa.DateTime(timezone=False), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('direction', sa.String(), nullable=False),
    sa.Column('account_id', sa.Integer(), sa.ForeignKey('chart_accounts.id')),
    sa.Column('reference', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'cash_closures',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('closure_date', sa.DateTime(timezone=False), index=True, nullable=False),
    sa.Column('counted_amount', sa.Float(), nullable=False),
    sa.Column('expected_amount', sa.Float(), nullable=False),
    sa.Column('difference', sa.Float(), nullable=False),
    sa.Column('status', cashclosurestatus_enum, nullable=False),
    sa.Column('notes', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('submitted_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('approved_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('approved_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'classes',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('level', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
    sa.Column('main_teacher_id', sa.Integer(), sa.ForeignKey('users.id')),
)

sa.Table(
    'government_exports',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('export_type', sa.String(), index=True, nullable=False),
    sa.Column('period', sa.String()),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('generated_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'leave_requests',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('staff_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('leave_type', sa.String(), nullable=False),
    sa.Column('start_date', sa.DateTime(timezone=False), nullable=False),
    sa.Column('end_date', sa.DateTime(timezone=False), nullable=False),
    sa.Column('reason', sa.String()),
    sa.Column('status', leavestatus_enum, nullable=False),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('decided_by_id', sa.Integer(), sa.ForeignKey('users.id')),
)

sa.Table(
    'loans',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('book_id', sa.Integer(), sa.ForeignKey('books.id'), nullable=False),
    sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('issue_date', sa.DateTime(timezone=False)),
    sa.Column('due_date', sa.DateTime(timezone=False), nullable=False),
    sa.Column('return_date', sa.DateTime(timezone=False)),
    sa.Column('status', loanstatus_enum),
    sa.Column('notes', sa.String()),
)

sa.Table(
    'notification_messages',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('channel', notificationchannel_enum, nullable=False),
    sa.Column('recipient', sa.String(), nullable=False),
    sa.Column('subject', sa.String()),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('provider_id', sa.Integer(), sa.ForeignKey('notification_providers.id')),
    sa.Column('status', notificationstatus_enum, nullable=False),
    sa.Column('provider_response', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('sent_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'payroll_records',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('staff_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('period', sa.String(), index=True, nullable=False),
    sa.Column('gross_amount', sa.Float(), nullable=False),
    sa.Column('deductions', sa.Float()),
    sa.Column('net_amount', sa.Float(), nullable=False),
    sa.Column('status', payrollstatus_enum, nullable=False),
    sa.Column('paid_at', sa.DateTime(timezone=True)),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'semesters',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('code', sa.String(), index=True, nullable=False),
    sa.Column('academic_year_id', sa.Integer(), sa.ForeignKey('academic_years.id')),
    sa.Column('start_date', sa.DateTime(timezone=False)),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'staff_contracts',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('staff_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('contract_type', sa.String(), nullable=False),
    sa.Column('start_date', sa.DateTime(timezone=False), nullable=False),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('base_salary', sa.Float()),
    sa.Column('cnss_number', sa.String()),
    sa.Column('tax_identifier', sa.String()),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'teacher_profiles',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True),
    sa.Column('specialization', sa.String()),
    sa.Column('join_date', sa.DateTime(timezone=False)),
    sa.Column('bio', sa.String()),
    sa.UniqueConstraint('user_id'),
)

sa.Table(
    'terms',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('start_date', sa.DateTime(timezone=False)),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('academic_year_id', sa.Integer(), sa.ForeignKey('academic_years.id')),
)

sa.Table(
    'vendor_invoices',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('vendor_name', sa.String(), nullable=False),
    sa.Column('invoice_number', sa.String(), index=True, nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=False)),
    sa.Column('status', invoicestatus_enum, nullable=False),
    sa.Column('account_id', sa.Integer(), sa.ForeignKey('chart_accounts.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'approval_steps',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('approval_workflows.id'), nullable=False),
    sa.Column('step_order', sa.Integer(), nullable=False),
    sa.Column('role', userrole_enum, nullable=False),
    sa.Column('approver_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('status', approvalstatus_enum, nullable=False),
    sa.Column('comment', sa.String()),
    sa.Column('decided_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'assessments',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('type', assessmenttype_enum),
    sa.Column('date', sa.DateTime(timezone=False), nullable=False),
    sa.Column('max_score', sa.Integer()),
    sa.Column('weight', sa.Integer()),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id'), nullable=False),
    sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id'), nullable=False),
    sa.Column('term_id', sa.Integer(), sa.ForeignKey('terms.id'), nullable=False),
)

sa.Table(
    'assignments',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('title', sa.String(), index=True, nullable=False),
    sa.Column('instructions', sa.String()),
    sa.Column('due_date', sa.DateTime(timezone=False)),
    sa.Column('status', assignmentstatus_enum, nullable=False),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id'), nullable=False),
    sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id')),
    sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'budget_forecasts',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('expected_students', sa.Integer()),
    sa.Column('expected_revenue', sa.Float()),
    sa.Column('fee_category', sa.String(), index=True),
    sa.Column('level', sa.String(), index=True),
    sa.Column('academic_year_id', sa.Integer(), sa.ForeignKey('academic_years.id')),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'course_materials',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('title', sa.String(), index=True, nullable=False),
    sa.Column('description', sa.String()),
    sa.Column('content_url', sa.String()),
    sa.Column('content_text', sa.String()),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id'), nullable=False),
    sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id')),
    sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'course_units',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('code', sa.String(), index=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('credits', sa.Float()),
    sa.Column('semester_id', sa.Integer(), sa.ForeignKey('semesters.id')),
    sa.Column('program_id', sa.Integer(), sa.ForeignKey('academic_programs.id')),
    sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'exam_sessions',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('exam_type', sa.String(), index=True, nullable=False),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id')),
    sa.Column('program_id', sa.Integer(), sa.ForeignKey('academic_programs.id')),
    sa.Column('start_date', sa.DateTime(timezone=False)),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'fee_schedules',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('name', sa.String(), index=True, nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('category_order', sa.Integer()),
    sa.Column('is_required', sa.Boolean()),
    sa.Column('is_current', sa.Boolean()),
    sa.Column('academic_year_id', sa.Integer(), sa.ForeignKey('academic_years.id')),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id')),
    sa.Column('level', sa.String(), index=True),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'payroll_adjustments',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('payroll_record_id', sa.Integer(), sa.ForeignKey('payroll_records.id'), nullable=False),
    sa.Column('adjustment_type', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('is_taxable', sa.Boolean()),
)

sa.Table(
    'student_profiles',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True),
    sa.Column('registration_number', sa.String(), index=True, unique=True),
    sa.Column('date_of_birth', sa.DateTime(timezone=False)),
    sa.Column('gender', sa.String()),
    sa.Column('student_address', sa.String()),
    sa.Column('parent_name', sa.String()),
    sa.Column('parent_phone', sa.String()),
    sa.Column('parent_email', sa.String()),
    sa.Column('parent_address', sa.String()),
    sa.Column('guardian_relation', sa.String()),
    sa.Column('status', studentstatus_enum, nullable=False),
    sa.Column('previous_level', sa.String()),
    sa.Column('previous_class', sa.String()),
    sa.Column('current_class_id', sa.Integer(), sa.ForeignKey('classes.id')),
    sa.UniqueConstraint('user_id'),
)

sa.Table(
    'timetables',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('day_of_week', dayofweek_enum, nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('room', sa.String()),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id'), nullable=False),
    sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id'), nullable=False),
    sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id')),
)

sa.Table(
    'administrative_requests',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('request_type', administrativerequesttype_enum, nullable=False),
    sa.Column('status', administrativerequeststatus_enum, nullable=False),
    sa.Column('details', sa.String()),
    sa.Column('response', sa.String()),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('requested_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('handled_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('handled_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'assignment_submissions',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('assignments.id'), nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('content_text', sa.String()),
    sa.Column('attachment_url', sa.String()),
    sa.Column('status', submissionstatus_enum, nullable=False),
    sa.Column('score', sa.Float()),
    sa.Column('feedback', sa.String()),
    sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('graded_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'attendance',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('date', sa.DateTime(timezone=False), index=True, nullable=False),
    sa.Column('status', attendancestatus_enum, nullable=False),
    sa.Column('remarks', sa.String()),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('timetable_id', sa.Integer(), sa.ForeignKey('timetables.id'), nullable=False),
    sa.Column('recorded_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'canteen_subscriptions',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('meal_plan_id', sa.Integer(), sa.ForeignKey('canteen_meal_plans.id'), nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('start_date', sa.DateTime(timezone=False)),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'certificate_requests',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('certificate_type', certificatetype_enum, nullable=False),
    sa.Column('status', certificatestatus_enum, nullable=False),
    sa.Column('blocked_reason', sa.String()),
    sa.Column('content', sa.String()),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('generated_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'certified_transcripts',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('semester_id', sa.Integer(), sa.ForeignKey('semesters.id')),
    sa.Column('total_credits', sa.Float()),
    sa.Column('gpa', sa.Float()),
    sa.Column('content', sa.JSON()),
    sa.Column('certificate_number', sa.String(), unique=True, nullable=False),
    sa.Column('is_certified', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('issued_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.UniqueConstraint('certificate_number'),
)

sa.Table(
    'diploma_records',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('program_id', sa.Integer(), sa.ForeignKey('academic_programs.id')),
    sa.Column('diploma_name', sa.String(), nullable=False),
    sa.Column('mention', sa.String()),
    sa.Column('issued_date', sa.DateTime(timezone=False)),
    sa.Column('certificate_number', sa.String(), unique=True, nullable=False),
    sa.Column('total_credits', sa.Float()),
    sa.Column('is_certified', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('issued_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.UniqueConstraint('certificate_number'),
)

sa.Table(
    'fees',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('title', sa.String(), index=True, nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=False)),
    sa.Column('status', feestatus_enum, nullable=False),
    sa.Column('description', sa.String()),
    sa.Column('category', sa.String(), index=True),
    sa.Column('category_order', sa.Integer()),
    sa.Column('is_required', sa.Boolean()),
    sa.Column('academic_year_id', sa.Integer(), sa.ForeignKey('academic_years.id')),
    sa.Column('class_id', sa.Integer(), sa.ForeignKey('classes.id')),
    sa.Column('covered_by', sa.JSON()),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
)

sa.Table(
    'grades',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('comment', sa.String()),
    sa.Column('assessment_id', sa.Integer(), sa.ForeignKey('assessments.id'), nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.UniqueConstraint('assessment_id', 'student_id', name='_assessment_student_uc'),
)

sa.Table(
    'internships',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('company_name', sa.String(), nullable=False),
    sa.Column('supervisor_name', sa.String()),
    sa.Column('start_date', sa.DateTime(timezone=False)),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('notes', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'parent_student_links',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('parent_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('relation', sa.String()),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.UniqueConstraint('parent_user_id', 'student_id', name='_parent_student_uc'),
)

sa.Table(
    'school_exits',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('reason', sa.String(), nullable=False),
    sa.Column('exit_date', sa.DateTime(timezone=False), nullable=False),
    sa.Column('destination', sa.String()),
    sa.Column('is_authorized', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'sms_messages',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('recipient_phone', sa.String(), nullable=False),
    sa.Column('recipient_name', sa.String()),
    sa.Column('event_type', sa.String(), index=True, nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'student_education_history',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('previous_school', sa.String(), nullable=False),
    sa.Column('class_level', sa.String(), nullable=False),
    sa.Column('degree_obtained', sa.String()),
    sa.Column('grade_average', sa.String()),
    sa.Column('year_completed', sa.Integer()),
)

sa.Table(
    'student_orientations',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('recommended_path', sa.String(), nullable=False),
    sa.Column('notes', sa.String()),
    sa.Column('decision_date', sa.DateTime(timezone=False)),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
    sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'student_registration_documents',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('is_received', sa.Boolean()),
    sa.Column('received_at', sa.DateTime(timezone=True)),
    sa.Column('notes', sa.String()),
    sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)

sa.Table(
    'transport_assignments',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('route_id', sa.Integer(), sa.ForeignKey('transport_routes.id'), nullable=False),
    sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id'), nullable=False),
    sa.Column('pickup_stop', sa.String()),
    sa.Column('dropoff_stop', sa.String()),
    sa.Column('start_date', sa.DateTime(timezone=False)),
    sa.Column('end_date', sa.DateTime(timezone=False)),
    sa.Column('is_active', sa.Boolean()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'university_schedule_slots',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('course_unit_id', sa.Integer(), sa.ForeignKey('course_units.id'), nullable=False),
    sa.Column('day_of_week', dayofweek_enum, nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('room', sa.String()),
    sa.Column('group_name', sa.String()),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'canteen_attendance',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('canteen_subscriptions.id'), nullable=False),
    sa.Column('served_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('served_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
)

sa.Table(
    'payments',
    BASE_METADATA,
    sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('payment_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('note', sa.String()),
    sa.Column('receipt_number', sa.String(), index=True, unique=True),
    sa.Column('operator_station', sa.String()),
    sa.Column('recorded_by_id', sa.Integer(), sa.ForeignKey('users.id')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('fee_id', sa.Integer(), sa.ForeignKey('fees.id'), nullable=False),
)


def upgrade():
    bind = op.get_bind()
    BASE_METADATA.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    BASE_METADATA.drop_all(bind=bind)
