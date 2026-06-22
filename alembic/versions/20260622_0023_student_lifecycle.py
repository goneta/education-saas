"""student lifecycle, transfers, academic locks, and enrollment scoping

Revision ID: 20260622_0023
Revises: 20260622_0022
Create Date: 2026-06-22
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "20260622_0023"
down_revision = "20260622_0022"
branch_labels = None
depends_on = None


ENROLLMENT_TABLES = (
    "grades",
    "attendance",
    "assignment_submissions",
    "internship_assignments",
    "fees",
    "payments",
    "student_invoices",
    "outstanding_balances",
    "cash_journal_entries",
    "generated_documents",
    "student_registration_documents",
    "certificate_requests",
    "ai_usage_logs",
)


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {row["name"] for row in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    tables = _tables()
    if "student_global_profiles" not in tables:
        op.create_table(
            "student_global_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("student_profile_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("global_student_number", sa.String(), nullable=False),
            sa.Column("first_name", sa.String(), nullable=False),
            sa.Column("last_name", sa.String(), nullable=False),
            sa.Column("date_of_birth", sa.DateTime(), nullable=True),
            sa.Column("gender", sa.String(), nullable=True),
            sa.Column("nationality", sa.String(), nullable=True),
            sa.Column("photo_url", sa.String(), nullable=True),
            sa.Column("identity_data", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("student_profile_id", name="uq_student_global_profiles_student_profile_id"),
            sa.UniqueConstraint("user_id", name="uq_student_global_profiles_user_id"),
            sa.UniqueConstraint("global_student_number", name="uq_student_global_profiles_global_student_number"),
        )
        op.create_index("ix_student_global_profiles_student_profile_id", "student_global_profiles", ["student_profile_id"], unique=True)
        op.create_index("ix_student_global_profiles_user_id", "student_global_profiles", ["user_id"], unique=True)
        op.create_index("ix_student_global_profiles_global_student_number", "student_global_profiles", ["global_student_number"], unique=True)
        op.create_index("ix_student_global_profiles_date_of_birth", "student_global_profiles", ["date_of_birth"])

    if "student_enrollments" not in _tables():
        op.create_table(
            "student_enrollments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("student_global_profile_id", sa.Integer(), sa.ForeignKey("student_global_profiles.id"), nullable=False),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("school_model_assignment_id", sa.Integer(), sa.ForeignKey("school_model_assignments.id"), nullable=False),
            sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=False),
            sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), nullable=True),
            sa.Column("level_id", sa.Integer(), nullable=True),
            sa.Column("program_id", sa.Integer(), sa.ForeignKey("academic_programs.id"), nullable=True),
            sa.Column("enrollment_status", sa.String(), nullable=False, server_default="active"),
            sa.Column("enrollment_type", sa.String(), nullable=False, server_default="full_time"),
            sa.Column("schedule_type", sa.String(), nullable=False, server_default="morning"),
            sa.Column("allows_concurrent_enrollment", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("primary_enrollment", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("module_id", sa.Integer(), nullable=True),
            sa.Column("training_program_id", sa.Integer(), sa.ForeignKey("academic_programs.id"), nullable=True),
            sa.Column("certification_id", sa.Integer(), nullable=True),
            sa.Column("start_date", sa.DateTime(), nullable=False),
            sa.Column("end_date", sa.DateTime(), nullable=True),
            sa.Column("start_time", sa.Time(), nullable=True),
            sa.Column("end_time", sa.Time(), nullable=True),
            sa.Column("days_of_week", sa.JSON(), nullable=True),
            sa.Column("location", sa.String(), nullable=True),
            sa.Column("transfer_from_school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
            sa.Column("transfer_to_school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("override_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint(
                "student_global_profile_id",
                "school_id",
                "school_model_assignment_id",
                "academic_year_id",
                "class_id",
                "program_id",
                name="_student_enrollment_context_uc",
            ),
        )
        for column in (
            "student_global_profile_id", "organization_id", "school_id",
            "school_model_assignment_id", "academic_year_id", "class_id",
            "level_id", "program_id", "enrollment_status", "enrollment_type",
            "schedule_type", "primary_enrollment", "module_id",
            "training_program_id", "certification_id",
        ):
            op.create_index(f"ix_student_enrollments_{column}", "student_enrollments", [column])

    if "student_transfer_requests" not in _tables():
        op.create_table(
            "student_transfer_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("student_global_profile_id", sa.Integer(), sa.ForeignKey("student_global_profiles.id"), nullable=False),
            sa.Column("from_organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("from_school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("from_school_model_assignment_id", sa.Integer(), sa.ForeignKey("school_model_assignments.id"), nullable=False),
            sa.Column("from_academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=False),
            sa.Column("to_organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("to_school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("to_school_model_assignment_id", sa.Integer(), sa.ForeignKey("school_model_assignments.id"), nullable=False),
            sa.Column("to_academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=False),
            sa.Column("requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("academic_data_access_level", sa.String(), nullable=False, server_default="summary"),
            sa.Column("financial_data_access_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        for column in (
            "student_global_profile_id", "from_organization_id", "from_school_id",
            "from_school_model_assignment_id", "from_academic_year_id",
            "to_organization_id", "to_school_id", "to_school_model_assignment_id",
            "to_academic_year_id", "status",
        ):
            op.create_index(f"ix_student_transfer_requests_{column}", "student_transfer_requests", [column])

    if "academic_year_locks" not in _tables():
        op.create_table(
            "academic_year_locks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("school_model_assignment_id", sa.Integer(), sa.ForeignKey("school_model_assignments.id"), nullable=True),
            sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="open"),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("closed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("unlock_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("unlock_reason", sa.Text(), nullable=True),
            sa.Column("unlocked_by_super_admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("school_id", "school_model_assignment_id", "academic_year_id", name="_academic_year_lock_context_uc"),
        )
        for column in ("organization_id", "school_id", "school_model_assignment_id", "academic_year_id", "status"):
            op.create_index(f"ix_academic_year_locks_{column}", "academic_year_locks", [column])

    if "historical_data_edit_grants" not in _tables():
        op.create_table(
            "historical_data_edit_grants",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("granted_by_super_admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=False),
            sa.Column("student_global_profile_id", sa.Integer(), sa.ForeignKey("student_global_profiles.id"), nullable=True),
            sa.Column("resource_type", sa.String(), nullable=True),
            sa.Column("resource_id", sa.Integer(), nullable=True),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        for column in (
            "granted_by_super_admin_id", "organization_id", "school_id",
            "academic_year_id", "student_global_profile_id", "resource_type",
            "resource_id", "valid_until", "is_active",
        ):
            op.create_index(f"ix_historical_data_edit_grants_{column}", "historical_data_edit_grants", [column])

    if "student_import_batches" not in _tables():
        op.create_table(
            "student_import_batches",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("school_model_assignment_id", sa.Integer(), sa.ForeignKey("school_model_assignments.id"), nullable=False),
            sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=False),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("source_format", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="preview"),
            sa.Column("preview_payload", sa.JSON(), nullable=False),
            sa.Column("error_payload", sa.JSON(), nullable=True),
            sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        for column in ("school_id", "school_model_assignment_id", "academic_year_id", "status"):
            op.create_index(f"ix_student_import_batches_{column}", "student_import_batches", [column])

    if "student_lifecycle_migration_reports" not in _tables():
        op.create_table(
            "student_lifecycle_migration_reports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("migration_revision", sa.String(), nullable=False),
            sa.Column("profiles_created", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("enrollments_created", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("records_linked", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("warnings", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("migration_revision", name="uq_student_lifecycle_migration_reports_revision"),
        )
        op.create_index("ix_student_lifecycle_migration_reports_revision", "student_lifecycle_migration_reports", ["migration_revision"], unique=True)

    for table in ENROLLMENT_TABLES:
        if table in _tables() and "student_enrollment_id" not in _columns(table):
            with op.batch_alter_table(table) as batch:
                batch.add_column(sa.Column("student_enrollment_id", sa.Integer(), nullable=True))
                batch.create_foreign_key(
                    f"fk_{table}_student_enrollment_id",
                    "student_enrollments",
                    ["student_enrollment_id"],
                    ["id"],
                )
                batch.create_index(f"ix_{table}_student_enrollment_id", ["student_enrollment_id"])

    profile_count = 0
    enrollment_count = 0
    linked_count = 0
    warnings = []
    legacy_students = bind.execute(sa.text(
        "SELECT sp.id AS student_profile_id, sp.user_id, sp.registration_number, sp.date_of_birth, "
        "sp.gender, sp.current_class_id, sp.school_model_assignment_id, u.full_name, u.school_id "
        "FROM student_profiles sp JOIN users u ON u.id = sp.user_id ORDER BY sp.id"
    )).mappings().all()
    for legacy in legacy_students:
        global_id = bind.execute(sa.text(
            "SELECT id FROM student_global_profiles WHERE student_profile_id = :student_profile_id"
        ), {"student_profile_id": legacy["student_profile_id"]}).scalar()
        if not global_id:
            names = (legacy["full_name"] or "Eleve").strip().split()
            first_name = names[0]
            last_name = " ".join(names[1:])
            global_number = f"TED-LEGACY-{legacy['student_profile_id']:08d}"
            bind.execute(sa.text(
                "INSERT INTO student_global_profiles "
                "(student_profile_id, user_id, global_student_number, first_name, last_name, date_of_birth, gender, created_at) "
                "VALUES (:student_profile_id, :user_id, :global_number, :first_name, :last_name, :date_of_birth, :gender, CURRENT_TIMESTAMP)"
            ), {
                "student_profile_id": legacy["student_profile_id"],
                "user_id": legacy["user_id"],
                "global_number": global_number,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": legacy["date_of_birth"],
                "gender": legacy["gender"],
            })
            global_id = bind.execute(sa.text(
                "SELECT id FROM student_global_profiles WHERE student_profile_id = :student_profile_id"
            ), {"student_profile_id": legacy["student_profile_id"]}).scalar()
            profile_count += 1
        school_id = legacy["school_id"]
        assignment_id = legacy["school_model_assignment_id"]
        if not school_id or not assignment_id:
            warnings.append({"student_profile_id": legacy["student_profile_id"], "warning": "missing school or model assignment"})
            continue
        organization_id = bind.execute(sa.text(
            "SELECT organization_id FROM schools WHERE id = :school_id"
        ), {"school_id": school_id}).scalar()
        year = bind.execute(sa.text(
            "SELECT id, start_date, end_date FROM academic_years "
            "WHERE school_id = :school_id AND school_model_assignment_id = :assignment_id "
            "ORDER BY is_current DESC, id DESC"
        ), {"school_id": school_id, "assignment_id": assignment_id}).mappings().first()
        if not year:
            current_year = datetime.utcnow().year
            bind.execute(sa.text(
                "INSERT INTO academic_years "
                "(name, start_date, end_date, is_current, school_id, school_model_assignment_id) "
                "VALUES (:name, :start_date, :end_date, :is_current, :school_id, :assignment_id)"
            ), {
                "name": f"{current_year}-{current_year + 1}",
                "start_date": datetime(current_year, 9, 1),
                "end_date": datetime(current_year + 1, 7, 31),
                "is_current": True,
                "school_id": school_id,
                "assignment_id": assignment_id,
            })
            year = bind.execute(sa.text(
                "SELECT id, start_date, end_date FROM academic_years "
                "WHERE school_id = :school_id AND school_model_assignment_id = :assignment_id ORDER BY id DESC"
            ), {"school_id": school_id, "assignment_id": assignment_id}).mappings().first()
        enrollment_id = bind.execute(sa.text(
            "SELECT id FROM student_enrollments WHERE student_global_profile_id = :global_id "
            "AND school_id = :school_id AND school_model_assignment_id = :assignment_id "
            "AND academic_year_id = :year_id ORDER BY id DESC"
        ), {
            "global_id": global_id,
            "school_id": school_id,
            "assignment_id": assignment_id,
            "year_id": year["id"],
        }).scalar()
        if not enrollment_id:
            bind.execute(sa.text(
                "INSERT INTO student_enrollments "
                "(student_global_profile_id, organization_id, school_id, school_model_assignment_id, academic_year_id, "
                "class_id, enrollment_status, enrollment_type, schedule_type, allows_concurrent_enrollment, "
                "primary_enrollment, start_date, end_date, created_at) "
                "VALUES (:global_id, :organization_id, :school_id, :assignment_id, :year_id, :class_id, "
                "'active', 'full_time', 'morning', :allows_concurrent, :primary_enrollment, :start_date, :end_date, CURRENT_TIMESTAMP)"
            ), {
                "global_id": global_id,
                "organization_id": organization_id,
                "school_id": school_id,
                "assignment_id": assignment_id,
                "year_id": year["id"],
                "class_id": legacy["current_class_id"],
                "allows_concurrent": False,
                "primary_enrollment": True,
                "start_date": year["start_date"] or datetime.utcnow(),
                "end_date": year["end_date"],
            })
            enrollment_id = bind.execute(sa.text(
                "SELECT id FROM student_enrollments WHERE student_global_profile_id = :global_id "
                "AND school_id = :school_id AND academic_year_id = :year_id ORDER BY id DESC"
            ), {"global_id": global_id, "school_id": school_id, "year_id": year["id"]}).scalar()
            enrollment_count += 1

        direct_student_tables = (
            "grades", "attendance", "assignment_submissions", "internship_assignments",
            "fees", "student_invoices", "outstanding_balances", "cash_journal_entries",
            "student_registration_documents", "certificate_requests",
        )
        for table in direct_student_tables:
            if table in _tables() and "student_id" in _columns(table):
                result = bind.execute(sa.text(
                    f"UPDATE {table} SET student_enrollment_id = :enrollment_id "
                    "WHERE student_id = :student_profile_id AND student_enrollment_id IS NULL"
                ), {"enrollment_id": enrollment_id, "student_profile_id": legacy["student_profile_id"]})
                linked_count += result.rowcount or 0

        if "payments" in _tables():
            result = bind.execute(sa.text(
                "UPDATE payments SET student_enrollment_id = :enrollment_id "
                "WHERE student_enrollment_id IS NULL AND fee_id IN "
                "(SELECT id FROM fees WHERE student_id = :student_profile_id)"
            ), {"enrollment_id": enrollment_id, "student_profile_id": legacy["student_profile_id"]})
            linked_count += result.rowcount or 0
        if "generated_documents" in _tables():
            result = bind.execute(sa.text(
                "UPDATE generated_documents SET student_enrollment_id = :enrollment_id "
                "WHERE student_enrollment_id IS NULL AND ("
                "(source_type = 'fee' AND source_id IN (SELECT id FROM fees WHERE student_id = :student_profile_id)) "
                "OR (source_type = 'invoice' AND source_id IN "
                "(SELECT id FROM student_invoices WHERE student_id = :student_profile_id))"
                ")"
            ), {"enrollment_id": enrollment_id, "student_profile_id": legacy["student_profile_id"]})
            linked_count += result.rowcount or 0

    bind.execute(sa.text(
        "INSERT INTO student_lifecycle_migration_reports "
        "(migration_revision, profiles_created, enrollments_created, records_linked, warnings, created_at) "
        "VALUES (:revision, :profiles, :enrollments, :linked, :warnings, CURRENT_TIMESTAMP)"
    ), {
        "revision": revision,
        "profiles": profile_count,
        "enrollments": enrollment_count,
        "linked": linked_count,
        "warnings": json_dumps(warnings),
    })


def json_dumps(value):
    import json
    return json.dumps(value)


def downgrade() -> None:
    for table in reversed(ENROLLMENT_TABLES):
        if table in _tables() and "student_enrollment_id" in _columns(table):
            with op.batch_alter_table(table) as batch:
                batch.drop_index(f"ix_{table}_student_enrollment_id")
                batch.drop_constraint(f"fk_{table}_student_enrollment_id", type_="foreignkey")
                batch.drop_column("student_enrollment_id")
    for table in (
        "student_lifecycle_migration_reports",
        "student_import_batches",
        "historical_data_edit_grants",
        "academic_year_locks",
        "student_transfer_requests",
        "student_enrollments",
        "student_global_profiles",
    ):
        if table in _tables():
            op.drop_table(table)
