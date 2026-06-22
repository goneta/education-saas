"""multi-school organizations, school models, and active context

Revision ID: 20260622_0022
Revises: 20260622_0021
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260622_0022"
down_revision = "20260622_0021"
branch_labels = None
depends_on = None


MODEL_ROWS = (
    ("PRIMARY", "Primaire", "Enseignement primaire"),
    ("GENERAL_SECONDARY", "General / Secondaire", "College et lycee general"),
    ("VOCATIONAL", "Vocationnel", "Formation vocationnelle"),
    ("TECHNICAL", "Technique", "Enseignement technique"),
    ("PROFESSIONAL", "Professionnel", "Formation professionnelle"),
    ("UNIVERSITY", "Universitaire", "Enseignement superieur"),
)


CONTEXT_TABLES = (
    "student_profiles",
    "teacher_profiles",
    "academic_years",
    "classes",
    "subjects",
    "academic_programs",
    "fees",
    "student_invoices",
    "outstanding_balances",
    "cash_journal_entries",
    "fee_schedules",
    "partner_companies",
    "internships",
    "ai_usage_logs",
    "school_payments",
)


SYSTEM_DEFAULT_TABLES = ("classes", "subjects", "academic_programs", "fee_schedules")


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {row["name"] for row in sa.inspect(op.get_bind()).get_columns(table)}


def _model_code(school_type: str | None) -> str:
    value = (school_type or "general").lower()
    return {
        "primary": "PRIMARY",
        "secondary": "GENERAL_SECONDARY",
        "general": "GENERAL_SECONDARY",
        "vocational": "VOCATIONAL",
        "technical": "TECHNICAL",
        "professional": "PROFESSIONAL",
        "university": "UNIVERSITY",
    }.get(value, "GENERAL_SECONDARY")


def upgrade() -> None:
    tables = _tables()
    if "organizations" not in tables:
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("legal_name", sa.String(), nullable=True),
            sa.Column("registration_number", sa.String(), nullable=True),
            sa.Column("logo_url", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("address", sa.String(), nullable=True),
            sa.Column("country", sa.String(), nullable=False, server_default="CI"),
            sa.Column("currency", sa.String(), nullable=False, server_default="XOF"),
            sa.Column("timezone", sa.String(), nullable=False, server_default="Africa/Abidjan"),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("subscription_plan", sa.String(), nullable=False, server_default="free"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("registration_number", name="uq_organizations_registration_number"),
        )
        op.create_index("ix_organizations_name", "organizations", ["name"])
        op.create_index("ix_organizations_owner_user_id", "organizations", ["owner_user_id"])
        op.create_index("ix_organizations_is_active", "organizations", ["is_active"])

    if "school_models" not in tables:
        op.create_table(
            "school_models",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("code", name="uq_school_models_code"),
        )
        op.create_index("ix_school_models_code", "school_models", ["code"], unique=True)
        op.create_index("ix_school_models_is_active", "school_models", ["is_active"])

    bind = op.get_bind()
    school_models = sa.table(
        "school_models",
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_system_template", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
    )
    existing_codes = {row[0] for row in bind.execute(sa.text("SELECT code FROM school_models"))}
    missing_models = [
        {"code": code, "name": name, "description": description, "is_system_template": True, "is_active": True}
        for code, name, description in MODEL_ROWS
        if code not in existing_codes
    ]
    if missing_models:
        op.bulk_insert(school_models, missing_models)

    if "organization_id" not in _columns("schools"):
        with op.batch_alter_table("schools") as batch:
            batch.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
            batch.create_foreign_key("fk_schools_organization_id", "organizations", ["organization_id"], ["id"])
            batch.create_index("ix_schools_organization_id", ["organization_id"])

    if "school_model_assignments" not in _tables():
        op.create_table(
            "school_model_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("school_model_id", sa.Integer(), sa.ForeignKey("school_models.id"), nullable=False),
            sa.Column("display_name", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("monthly_ai_credit_limit", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("school_id", "school_model_id", name="_school_model_assignment_uc"),
        )
        op.create_index("ix_school_model_assignments_school_id", "school_model_assignments", ["school_id"])
        op.create_index("ix_school_model_assignments_school_model_id", "school_model_assignments", ["school_model_id"])
        op.create_index("ix_school_model_assignments_is_active", "school_model_assignments", ["is_active"])

    schools = bind.execute(sa.text(
        "SELECT id, name, school_type, country_code, currency_code, timezone, organization_id, "
        "subscription_plan FROM schools ORDER BY id"
    )).mappings().all()
    for school in schools:
        organization_id = school.get("organization_id")
        if not organization_id:
            organization_id = bind.execute(
                sa.text(
                    "INSERT INTO organizations "
                    "(name, country, currency, timezone, subscription_plan, is_active, created_at) "
                    "VALUES (:name, :country, :currency, :timezone, :plan, :active, CURRENT_TIMESTAMP)"
                ),
                {
                    "name": school["name"],
                    "country": school["country_code"] or "CI",
                    "currency": school["currency_code"] or "XOF",
                    "timezone": school["timezone"] or "Africa/Abidjan",
                    "plan": school["subscription_plan"] or "free",
                    "active": True,
                },
            ).lastrowid
            if not organization_id:
                organization_id = bind.execute(
                    sa.text("SELECT id FROM organizations WHERE name = :name ORDER BY id DESC"),
                    {"name": school["name"]},
                ).scalar()
            bind.execute(
                sa.text("UPDATE schools SET organization_id = :organization_id WHERE id = :school_id"),
                {"organization_id": organization_id, "school_id": school["id"]},
            )

        model_code = _model_code(str(school["school_type"]))
        model_id = bind.execute(
            sa.text("SELECT id FROM school_models WHERE code = :code"),
            {"code": model_code},
        ).scalar()
        exists = bind.execute(
            sa.text(
                "SELECT id FROM school_model_assignments "
                "WHERE school_id = :school_id AND school_model_id = :model_id"
            ),
            {"school_id": school["id"], "model_id": model_id},
        ).scalar()
        if not exists:
            bind.execute(
                sa.text(
                    "INSERT INTO school_model_assignments "
                    "(school_id, school_model_id, display_name, is_active, ai_enabled, created_at) "
                    "VALUES (:school_id, :model_id, :display_name, :active, :ai_enabled, CURRENT_TIMESTAMP)"
                ),
                {
                    "school_id": school["id"],
                    "model_id": model_id,
                    "display_name": model_code.replace("_", " ").title(),
                    "active": True,
                    "ai_enabled": True,
                },
            )

    for table in CONTEXT_TABLES:
        if table in _tables() and "school_model_assignment_id" not in _columns(table):
            with op.batch_alter_table(table) as batch:
                batch.add_column(sa.Column("school_model_assignment_id", sa.Integer(), nullable=True))
                batch.create_foreign_key(
                    f"fk_{table}_school_model_assignment_id",
                    "school_model_assignments",
                    ["school_model_assignment_id"],
                    ["id"],
                )
                batch.create_index(f"ix_{table}_school_model_assignment_id", ["school_model_assignment_id"])

    for table in SYSTEM_DEFAULT_TABLES:
        if table in _tables() and "is_system_default" not in _columns(table):
            with op.batch_alter_table(table) as batch:
                batch.add_column(sa.Column("is_system_default", sa.Boolean(), nullable=False, server_default=sa.false()))

    preference_columns = {
        "active_organization_id": "organizations",
        "active_school_id": "schools",
        "active_school_model_assignment_id": "school_model_assignments",
        "active_academic_year_id": "academic_years",
    }
    for column, target in preference_columns.items():
        if column not in _columns("user_preferences"):
            with op.batch_alter_table("user_preferences") as batch:
                batch.add_column(sa.Column(column, sa.Integer(), nullable=True))
                batch.create_foreign_key(f"fk_user_preferences_{column}", target, [column], ["id"])
                batch.create_index(f"ix_user_preferences_{column}", [column])

    audit_columns = {
        "organization_id": "organizations",
        "school_model_assignment_id": "school_model_assignments",
    }
    for column, target in audit_columns.items():
        if column not in _columns("audit_logs"):
            with op.batch_alter_table("audit_logs") as batch:
                batch.add_column(sa.Column(column, sa.Integer(), nullable=True))
                batch.create_foreign_key(f"fk_audit_logs_{column}", target, [column], ["id"])
                batch.create_index(f"ix_audit_logs_{column}", [column])

    for table in CONTEXT_TABLES:
        if table not in _tables() or "school_model_assignment_id" not in _columns(table):
            continue
        if "school_id" in _columns(table):
            bind.execute(sa.text(
                f"UPDATE {table} SET school_model_assignment_id = ("
                "SELECT sma.id FROM school_model_assignments sma "
                f"WHERE sma.school_id = {table}.school_id AND sma.is_active = TRUE "
                "ORDER BY sma.id LIMIT 1"
                ") WHERE school_model_assignment_id IS NULL"
            ))
        elif table in {"student_profiles", "teacher_profiles"}:
            bind.execute(sa.text(
                f"UPDATE {table} SET school_model_assignment_id = ("
                "SELECT sma.id FROM users u "
                "JOIN school_model_assignments sma ON sma.school_id = u.school_id "
                f"WHERE u.id = {table}.user_id AND sma.is_active = TRUE "
                "ORDER BY sma.id LIMIT 1"
                ") WHERE school_model_assignment_id IS NULL"
            ))

    bind.execute(sa.text(
        "UPDATE user_preferences SET "
        "active_school_id = (SELECT school_id FROM users WHERE users.id = user_preferences.user_id), "
        "active_organization_id = (SELECT schools.organization_id FROM users "
        "JOIN schools ON schools.id = users.school_id WHERE users.id = user_preferences.user_id), "
        "active_school_model_assignment_id = (SELECT sma.id FROM users "
        "JOIN school_model_assignments sma ON sma.school_id = users.school_id "
        "WHERE users.id = user_preferences.user_id AND sma.is_active = TRUE ORDER BY sma.id LIMIT 1) "
        "WHERE active_school_id IS NULL"
    ))


def downgrade() -> None:
    for column in ("school_model_assignment_id", "organization_id"):
        if "audit_logs" in _tables() and column in _columns("audit_logs"):
            with op.batch_alter_table("audit_logs") as batch:
                batch.drop_index(f"ix_audit_logs_{column}")
                batch.drop_constraint(f"fk_audit_logs_{column}", type_="foreignkey")
                batch.drop_column(column)

    for column in (
        "active_academic_year_id",
        "active_school_model_assignment_id",
        "active_school_id",
        "active_organization_id",
    ):
        if column in _columns("user_preferences"):
            with op.batch_alter_table("user_preferences") as batch:
                batch.drop_index(f"ix_user_preferences_{column}")
                batch.drop_constraint(f"fk_user_preferences_{column}", type_="foreignkey")
                batch.drop_column(column)

    for table in SYSTEM_DEFAULT_TABLES:
        if table in _tables() and "is_system_default" in _columns(table):
            with op.batch_alter_table(table) as batch:
                batch.drop_column("is_system_default")

    for table in reversed(CONTEXT_TABLES):
        if table in _tables() and "school_model_assignment_id" in _columns(table):
            with op.batch_alter_table(table) as batch:
                batch.drop_index(f"ix_{table}_school_model_assignment_id")
                batch.drop_constraint(f"fk_{table}_school_model_assignment_id", type_="foreignkey")
                batch.drop_column("school_model_assignment_id")

    if "school_model_assignments" in _tables():
        op.drop_table("school_model_assignments")
    if "organization_id" in _columns("schools"):
        with op.batch_alter_table("schools") as batch:
            batch.drop_index("ix_schools_organization_id")
            batch.drop_constraint("fk_schools_organization_id", type_="foreignkey")
            batch.drop_column("organization_id")
    if "school_models" in _tables():
        op.drop_table("school_models")
    if "organizations" in _tables():
        op.drop_table("organizations")
