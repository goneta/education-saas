"""Expand employment ATS fields.

Revision ID: 20260625_0028
Revises: 20260624_0027
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260625_0028"
down_revision = "20260624_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student_cvs", sa.Column("academic_credentials", sa.JSON(), nullable=True))
    op.add_column("student_cvs", sa.Column("certificates", sa.JSON(), nullable=True))
    op.add_column("student_cvs", sa.Column("detailed_skills", sa.JSON(), nullable=True))
    op.add_column("student_cvs", sa.Column("desired_location", sa.String(), nullable=True))
    op.add_column("student_cvs", sa.Column("total_experience_years", sa.Float(), nullable=False, server_default="0"))
    op.add_column("student_cv_work_history", sa.Column("technologies_used", sa.JSON(), nullable=True))
    op.add_column("student_cv_work_history", sa.Column("skills_acquired", sa.JSON(), nullable=True))

    op.add_column("recruiter_profiles", sa.Column("logo_url", sa.Text(), nullable=True))
    op.add_column("recruiter_profiles", sa.Column("company_description", sa.Text(), nullable=True))
    op.add_column("recruiter_profiles", sa.Column("subscription_duration_months", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("recruiter_profiles", sa.Column("subscription_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("recruiter_profiles", sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("recruiter_profiles", sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("recruiter_profiles", sa.Column("ai_credits_balance", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_recruiter_profiles_subscription_expires_at", "recruiter_profiles", ["subscription_expires_at"])

    op.add_column("job_offers", sa.Column("application_start_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("job_offers", sa.Column("desired_skills", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("required_languages", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("salary_fixed", sa.Float(), nullable=True))
    op.add_column("job_offers", sa.Column("salary_min", sa.Float(), nullable=True))
    op.add_column("job_offers", sa.Column("salary_max", sa.Float(), nullable=True))
    op.add_column("job_offers", sa.Column("currency", sa.String(), nullable=False, server_default="FCFA"))
    op.add_column("job_offers", sa.Column("contract_type", sa.String(), nullable=True))
    op.add_column("job_offers", sa.Column("minimum_academic_level", sa.String(), nullable=True))
    op.add_column("job_offers", sa.Column("required_years_experience", sa.Float(), nullable=True))
    op.add_column("job_offers", sa.Column("positions_count", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("job_offers", sa.Column("desired_start_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("job_offers", sa.Column("ai_match_summary", sa.JSON(), nullable=True))

    op.add_column("job_applications", sa.Column("ai_match_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("job_applications", sa.Column("ai_match_details", sa.JSON(), nullable=True))

    op.create_table(
        "employment_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("recruiter_id", sa.Integer(), nullable=True),
        sa.Column("student_cv_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recruiter_id"], ["recruiter_profiles.id"]),
        sa.ForeignKeyConstraint(["student_cv_id"], ["student_cvs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_employment_notifications_audience", "employment_notifications", ["audience"])
    op.create_index("ix_employment_notifications_created_at", "employment_notifications", ["created_at"])
    op.create_index("ix_employment_notifications_recruiter_id", "employment_notifications", ["recruiter_id"])
    op.create_index("ix_employment_notifications_student_cv_id", "employment_notifications", ["student_cv_id"])


def downgrade() -> None:
    op.drop_index("ix_employment_notifications_student_cv_id", table_name="employment_notifications")
    op.drop_index("ix_employment_notifications_recruiter_id", table_name="employment_notifications")
    op.drop_index("ix_employment_notifications_created_at", table_name="employment_notifications")
    op.drop_index("ix_employment_notifications_audience", table_name="employment_notifications")
    op.drop_table("employment_notifications")

    op.drop_column("job_applications", "ai_match_details")
    op.drop_column("job_applications", "ai_match_score")

    for column in [
        "ai_match_summary",
        "desired_start_date",
        "positions_count",
        "required_years_experience",
        "minimum_academic_level",
        "contract_type",
        "currency",
        "salary_max",
        "salary_min",
        "salary_fixed",
        "required_languages",
        "desired_skills",
        "application_start_at",
    ]:
        op.drop_column("job_offers", column)

    op.drop_index("ix_recruiter_profiles_subscription_expires_at", table_name="recruiter_profiles")
    for column in [
        "ai_credits_balance",
        "auto_renew",
        "subscription_expires_at",
        "subscription_started_at",
        "subscription_duration_months",
        "company_description",
        "logo_url",
    ]:
        op.drop_column("recruiter_profiles", column)

    op.drop_column("student_cv_work_history", "skills_acquired")
    op.drop_column("student_cv_work_history", "technologies_used")

    for column in ["total_experience_years", "desired_location", "detailed_skills", "certificates", "academic_credentials"]:
        op.drop_column("student_cvs", column)
