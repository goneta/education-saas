"""Vie scolaire: Discipline, Examens, Activités, Santé scolaire, Internat.

Five new school-scoped tables (discipline_records, exam_sessions,
school_activities, health_records, boarding_records) + global seeds for the
three new reference categories they consume (activity_type, incident_type,
health_record_type). New tables only, inline column FKs, idempotent.

Revision ID: 20260805_0056
Revises: 20260805_0055
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260805_0056"
down_revision = "20260805_0055"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


GLOBAL_SEEDS: dict[str, list[tuple[str, str]]] = {
    "activity_type": [
        ("OUTING", "Sortie scolaire"),
        ("CLUB", "Club / Atelier"),
        ("SPORT", "Activité sportive"),
        ("CULTURE", "Activité culturelle"),
        ("COMPETITION", "Compétition / Concours"),
        ("CEREMONY", "Cérémonie / Événement"),
        ("COMMUNITY", "Action citoyenne"),
    ],
    "incident_type": [
        ("VIOLENCE", "Violence / Bagarre"),
        ("BULLYING", "Harcèlement"),
        ("CHEATING", "Tricherie / Fraude"),
        ("VANDALISM", "Dégradation de matériel"),
        ("TRUANCY", "Absentéisme / Fugue"),
        ("DISRESPECT", "Insolence / Irrespect"),
        ("OTHER_INCIDENT", "Autre incident"),
    ],
    "health_record_type": [
        ("MEDICAL_VISIT", "Visite médicale"),
        ("VACCINATION", "Vaccination"),
        ("ALLERGY", "Allergie"),
        ("CHRONIC_CONDITION", "Maladie chronique"),
        ("INJURY", "Blessure / Accident"),
        ("MEDICATION", "Traitement en cours"),
        ("EMERGENCY", "Urgence médicale"),
    ],
}


def _table_specs() -> dict[str, list[sa.Column]]:
    return {
        "discipline_records": [
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
            sa.Column("record_kind", sa.String(), nullable=False),
            sa.Column("type_code", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("record_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="open"),
            sa.Column("decided_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ],
        "school_activities": [
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("activity_type_code", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("location", sa.String(), nullable=True),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), nullable=True),
            sa.Column("responsible_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("capacity", sa.Integer(), nullable=True),
            sa.Column("fee_amount", sa.Float(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="planned"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ],
        "health_records": [
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
            sa.Column("record_type_code", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("record_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("severity", sa.String(), nullable=True),
            sa.Column("treated_by", sa.String(), nullable=True),
            sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("status", sa.String(), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ],
        "boarding_records": [
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
            sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=True),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="active"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ],
    }


def upgrade() -> None:
    for table, columns in _table_specs().items():
        if not _has_table(table):
            op.create_table(table, *columns)
            op.create_index(f"ix_{table}_school_id", table, ["school_id"])
            if any(column.name == "student_id" for column in columns):
                op.create_index(f"ix_{table}_student_id", table, ["student_id"])
            op.create_index(f"ix_{table}_status", table, ["status"])

    # Examens: the EXISTING exam_sessions table (legacy operations planning) is
    # extended column-only for the Scolarité module — zero duplication.
    inspector = sa.inspect(op.get_bind())
    if _has_table("exam_sessions"):
        existing_columns = {column["name"] for column in inspector.get_columns("exam_sessions")}
        additions = [
            # plain Integer (no inline FK): SQLite cannot ALTER-add a
            # constrained column; the ORM relationship handles the join.
            sa.Column("subject_id", sa.Integer(), nullable=True),
            sa.Column("duration_minutes", sa.Integer(), nullable=True),
            sa.Column("room", sa.String(), nullable=True),
            sa.Column("max_score", sa.Float(), nullable=True),
            sa.Column("coefficient", sa.Float(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
        ]
        for column in additions:
            if column.name not in existing_columns:
                op.add_column("exam_sessions", column)

    bind = op.get_bind()
    existing = {
        (row[0], row[1])
        for row in bind.execute(sa.text(
            "SELECT category, code FROM reference_items WHERE school_id IS NULL"
        ))
    }
    for category, entries in GLOBAL_SEEDS.items():
        for order, (code, name) in enumerate(entries):
            if (category, code) in existing:
                continue
            bind.execute(
                sa.text(
                    "INSERT INTO reference_items (category, code, name, sort_order, is_active) "
                    "VALUES (:category, :code, :name, :sort_order, 1)"
                ),
                {"category": category, "code": code, "name": name, "sort_order": order},
            )


def downgrade() -> None:
    for table in _table_specs():
        if _has_table(table):
            op.drop_table(table)
