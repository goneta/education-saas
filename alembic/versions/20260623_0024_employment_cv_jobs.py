"""Add TeducAI employment CV and jobs module.

Revision ID: 20260623_0024
Revises: 20260622_0023
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260623_0024"
down_revision = "20260622_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_cvs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_global_profile_id", sa.Integer(), sa.ForeignKey("student_global_profiles.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("sharecode", sa.String(), nullable=False),
        sa.Column("share_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_external", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("professional_title", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sectors", sa.JSON(), nullable=True),
        sa.Column("looking_for_job", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cv_photo_url", sa.String(), nullable=True),
        sa.Column("privacy_settings", sa.JSON(), nullable=True),
        sa.Column("academic_timeline", sa.JSON(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("portfolio", sa.JSON(), nullable=True),
        sa.Column("availability", sa.String(), nullable=True),
        sa.Column("external_identity", sa.JSON(), nullable=True),
        sa.Column("last_auto_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_student_cvs_student_global_profile_id", "student_cvs", ["student_global_profile_id"])
    op.create_index("ix_student_cvs_user_id", "student_cvs", ["user_id"])
    op.create_index("ix_student_cvs_sharecode", "student_cvs", ["sharecode"], unique=True)
    op.create_index("ix_student_cvs_looking_for_job", "student_cvs", ["looking_for_job"])

    op.create_table(
        "student_cv_work_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_cv_id", sa.Integer(), sa.ForeignKey("student_cvs.id"), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("position", sa.String(), nullable=False),
        sa.Column("experience_type", sa.String(), nullable=False, server_default="stage"),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("missions", sa.JSON(), nullable=True),
        sa.Column("skills_used", sa.JSON(), nullable=True),
        sa.Column("proof_document_url", sa.String(), nullable=True),
        sa.Column("reference_contact", sa.String(), nullable=True),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_by_entity", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_student_cv_work_history_student_cv_id", "student_cv_work_history", ["student_cv_id"])

    op.create_table(
        "recruiter_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("contact_name", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("subscription_plan", sa.String(), nullable=False, server_default="sharecode_only"),
        sa.Column("payment_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("offers_allowed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cv_views_allowed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cv_views_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_recruiter_profiles_user_id", "recruiter_profiles", ["user_id"], unique=True)
    op.create_index("ix_recruiter_profiles_sector", "recruiter_profiles", ["sector"])

    op.create_table(
        "employment_subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=False, server_default="FCFA"),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("job_offer_limit", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cv_view_limit", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sharecode_access", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("cv_search_access", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_employment_subscription_plans_key", "employment_subscription_plans", ["key"], unique=True)

    op.create_table(
        "job_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recruiter_id", sa.Integer(), sa.ForeignKey("recruiter_profiles.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("sector", sa.String(), nullable=False),
        sa.Column("offer_type", sa.String(), nullable=False, server_default="emploi"),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("workplace_mode", sa.String(), nullable=False, server_default="on_site"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("missions", sa.JSON(), nullable=True),
        sa.Column("required_skills", sa.JSON(), nullable=True),
        sa.Column("required_degree", sa.String(), nullable=True),
        sa.Column("required_level", sa.String(), nullable=True),
        sa.Column("required_experience", sa.String(), nullable=True),
        sa.Column("salary", sa.String(), nullable=True),
        sa.Column("deadline", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_offers_recruiter_id", "job_offers", ["recruiter_id"])
    op.create_index("ix_job_offers_sector", "job_offers", ["sector"])
    op.create_index("ix_job_offers_status", "job_offers", ["status"])

    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_cv_id", sa.Integer(), sa.ForeignKey("student_cvs.id"), nullable=False),
        sa.Column("job_offer_id", sa.Integer(), sa.ForeignKey("job_offers.id"), nullable=False),
        sa.Column("motivation_message", sa.Text(), nullable=True),
        sa.Column("attached_documents", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="submitted"),
        sa.Column("status_history", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_cv_id", "job_offer_id", name="_job_application_cv_offer_uc"),
    )
    op.create_index("ix_job_applications_student_cv_id", "job_applications", ["student_cv_id"])
    op.create_index("ix_job_applications_job_offer_id", "job_applications", ["job_offer_id"])

    op.create_table(
        "job_interviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recruiter_id", sa.Integer(), sa.ForeignKey("recruiter_profiles.id"), nullable=False),
        sa.Column("student_cv_id", sa.Integer(), sa.ForeignKey("student_cvs.id"), nullable=False),
        sa.Column("job_application_id", sa.Integer(), sa.ForeignKey("job_applications.id"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("mode", sa.String(), nullable=False, server_default="presentiel"),
        sa.Column("location_or_link", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_interviews_student_cv_id", "job_interviews", ["student_cv_id"])
    op.create_index("ix_job_interviews_recruiter_id", "job_interviews", ["recruiter_id"])
    op.create_index("ix_job_interviews_job_application_id", "job_interviews", ["job_application_id"])

    op.create_table(
        "student_cv_access_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_cv_id", sa.Integer(), sa.ForeignKey("student_cvs.id"), nullable=False),
        sa.Column("recruiter_id", sa.Integer(), sa.ForeignKey("recruiter_profiles.id"), nullable=True),
        sa.Column("access_type", sa.String(), nullable=False),
        sa.Column("sharecode_used", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_student_cv_access_logs_student_cv_id", "student_cv_access_logs", ["student_cv_id"])
    op.create_index("ix_student_cv_access_logs_ip_address", "student_cv_access_logs", ["ip_address"])
    op.create_index("ix_student_cv_access_logs_created_at", "student_cv_access_logs", ["created_at"])

    op.bulk_insert(
        sa.table(
            "employment_subscription_plans",
            sa.column("key", sa.String()),
            sa.column("name", sa.String()),
            sa.column("price", sa.Float()),
            sa.column("currency", sa.String()),
            sa.column("duration_days", sa.Integer()),
            sa.column("job_offer_limit", sa.Integer()),
            sa.column("cv_view_limit", sa.Integer()),
            sa.column("sharecode_access", sa.Boolean()),
            sa.column("cv_search_access", sa.Boolean()),
            sa.column("is_active", sa.Boolean()),
        ),
        [
            {"key": "promo", "name": "Gratuit / promo", "price": 0, "currency": "FCFA", "duration_days": 30, "job_offer_limit": 1, "cv_view_limit": 10, "sharecode_access": True, "cv_search_access": False, "is_active": True},
            {"key": "sharecode_only", "name": "Acces sharecode", "price": 0, "currency": "FCFA", "duration_days": 30, "job_offer_limit": 0, "cv_view_limit": 25, "sharecode_access": True, "cv_search_access": False, "is_active": True},
            {"key": "job_posts", "name": "Publication d'offres", "price": 0, "currency": "FCFA", "duration_days": 30, "job_offer_limit": 5, "cv_view_limit": 50, "sharecode_access": True, "cv_search_access": False, "is_active": True},
            {"key": "cvtheque_limited", "name": "CVtheque limitee", "price": 0, "currency": "FCFA", "duration_days": 30, "job_offer_limit": 3, "cv_view_limit": 100, "sharecode_access": True, "cv_search_access": True, "is_active": True},
            {"key": "cvtheque_advanced", "name": "CVtheque avancee", "price": 0, "currency": "FCFA", "duration_days": 30, "job_offer_limit": 20, "cv_view_limit": 1000, "sharecode_access": True, "cv_search_access": True, "is_active": True},
        ],
    )


def downgrade() -> None:
    op.drop_table("student_cv_access_logs")
    op.drop_table("job_interviews")
    op.drop_table("job_applications")
    op.drop_table("job_offers")
    op.drop_table("employment_subscription_plans")
    op.drop_table("recruiter_profiles")
    op.drop_table("student_cv_work_history")
    op.drop_table("student_cvs")
