"""internship management module

Revision ID: 20260608_0013
Revises: 20260607_0012
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260608_0013"
down_revision = "20260607_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("rccm_number", sa.String(), nullable=True),
        sa.Column("tax_number", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("hr_manager_name", sa.String(), nullable=True),
        sa.Column("hr_manager_role", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("max_simultaneous_interns", sa.Integer(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("partnership_file_id", sa.Integer(), sa.ForeignKey("secure_files.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ["name", "industry", "city", "country", "status", "school_id"]:
        op.create_index(f"ix_partner_companies_{column}", "partner_companies", [column])

    with op.batch_alter_table("internships") as batch_op:
        batch_op.alter_column("student_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("company_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("academic_level", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("class_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("program", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("training_program", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("title", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("objectives", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("service_department", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("supervisor_role", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("supervisor_phone", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("supervisor_email", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("teacher_ref_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("pedagogy_coordinator_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("internship_manager_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("weeks_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("expected_schedule", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("ai_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("final_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key("fk_internships_company_id_partner_companies", "partner_companies", ["company_id"], ["id"])
        batch_op.create_foreign_key("fk_internships_class_id_classes", "classes", ["class_id"], ["id"])
        batch_op.create_foreign_key("fk_internships_teacher_ref_id_users", "users", ["teacher_ref_id"], ["id"])
        batch_op.create_foreign_key("fk_internships_pedagogy_coordinator_id_users", "users", ["pedagogy_coordinator_id"], ["id"])
        batch_op.create_foreign_key("fk_internships_internship_manager_id_users", "users", ["internship_manager_id"], ["id"])

    op.create_index("ix_internships_company_id", "internships", ["company_id"])
    op.create_index("ix_internships_academic_level", "internships", ["academic_level"])
    op.create_index("ix_internships_class_id", "internships", ["class_id"])

    op.create_table(
        "internship_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internships.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="assigned"),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("internship_id", "student_id", name="_internship_student_uc"),
    )
    for column in ["internship_id", "student_id", "status", "school_id"]:
        op.create_index(f"ix_internship_assignments_{column}", "internship_assignments", [column])

    op.create_table(
        "internship_daily_followups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internships.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("presence_status", sa.String(), nullable=False, server_default="present"),
        sa.Column("activities", sa.Text(), nullable=True),
        sa.Column("tasks_description", sa.Text(), nullable=True),
        sa.Column("developed_skills", sa.Text(), nullable=True),
        sa.Column("tools_used", sa.Text(), nullable=True),
        sa.Column("difficulties", sa.Text(), nullable=True),
        sa.Column("supervisor_observation", sa.Text(), nullable=True),
        sa.Column("supervisor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for column in ["internship_id", "student_id", "date", "school_id"]:
        op.create_index(f"ix_internship_daily_followups_{column}", "internship_daily_followups", [column])

    op.create_table(
        "internship_logbook_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internships.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("tasks_done", sa.Text(), nullable=True),
        sa.Column("acquired_skills", sa.Text(), nullable=True),
        sa.Column("difficulties", sa.Text(), nullable=True),
        sa.Column("proposed_solutions", sa.Text(), nullable=True),
        sa.Column("hours_count", sa.Float(), nullable=True),
        sa.Column("validation_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("supervisor_comment", sa.Text(), nullable=True),
        sa.Column("validated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ["internship_id", "student_id", "date", "validation_status", "school_id"]:
        op.create_index(f"ix_internship_logbook_entries_{column}", "internship_logbook_entries", [column])

    op.create_table(
        "internship_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internships.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True),
        sa.Column("evaluation_type", sa.String(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("company_score", sa.Float(), nullable=True),
        sa.Column("report_score", sa.Float(), nullable=True),
        sa.Column("defense_score", sa.Float(), nullable=True),
        sa.Column("practical_score", sa.Float(), nullable=True),
        sa.Column("final_score", sa.Float(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("evaluator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for column in ["internship_id", "student_id", "evaluation_type", "school_id"]:
        op.create_index(f"ix_internship_evaluations_{column}", "internship_evaluations", [column])

    op.create_table(
        "internship_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internships.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("secure_file_id", sa.Integer(), sa.ForeignKey("secure_files.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="available"),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for column in ["internship_id", "student_id", "document_type", "status", "school_id"]:
        op.create_index(f"ix_internship_documents_{column}", "internship_documents", [column])


def downgrade() -> None:
    for table_name in [
        "internship_documents",
        "internship_evaluations",
        "internship_logbook_entries",
        "internship_daily_followups",
        "internship_assignments",
    ]:
        op.drop_table(table_name)
    op.drop_index("ix_internships_class_id", table_name="internships")
    op.drop_index("ix_internships_academic_level", table_name="internships")
    op.drop_index("ix_internships_company_id", table_name="internships")
    with op.batch_alter_table("internships") as batch_op:
        for constraint in [
            "fk_internships_internship_manager_id_users",
            "fk_internships_pedagogy_coordinator_id_users",
            "fk_internships_teacher_ref_id_users",
            "fk_internships_class_id_classes",
            "fk_internships_company_id_partner_companies",
        ]:
            batch_op.drop_constraint(constraint, type_="foreignkey")
        for column in [
            "updated_at", "final_score", "ai_summary", "expected_schedule", "weeks_count",
            "internship_manager_id", "pedagogy_coordinator_id", "teacher_ref_id",
            "supervisor_email", "supervisor_phone", "supervisor_role", "service_department",
            "objectives", "description", "title", "training_program", "program", "class_id",
            "academic_level", "company_id",
        ]:
            batch_op.drop_column(column)
        batch_op.alter_column("student_id", existing_type=sa.Integer(), nullable=False)
    op.drop_table("partner_companies")
