from sqlalchemy import inspect, text


def ensure_runtime_schema(engine):
    """Small additive migration helper for the SQLite MVP database."""
    inspector = inspect(engine)

    def add_column(table_name: str, column_name: str, ddl: str):
        if table_name not in inspector.get_table_names():
            return
        existing = {column["name"] for column in inspector.get_columns(table_name)}
        if column_name not in existing:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))

    add_column("student_profiles", "guardian_relation", "VARCHAR")
    add_column("student_profiles", "status", "VARCHAR DEFAULT 'UNASSIGNED' NOT NULL")
    add_column("student_profiles", "previous_level", "VARCHAR")
    add_column("student_profiles", "previous_class", "VARCHAR")

    add_column("fees", "category", "VARCHAR")
    add_column("fees", "title", "VARCHAR DEFAULT 'Frais scolaire'")
    add_column("fees", "school_id", "INTEGER")
    add_column("fees", "category_order", "INTEGER DEFAULT 0")
    add_column("fees", "is_required", "BOOLEAN DEFAULT 1")
    add_column("fees", "academic_year_id", "INTEGER")
    add_column("fees", "class_id", "INTEGER")
    add_column("fees", "covered_by", "JSON")

    add_column("payments", "receipt_number", "VARCHAR")
    add_column("payments", "note", "VARCHAR")
    add_column("payments", "operator_station", "VARCHAR")
    add_column("payments", "recorded_by_id", "INTEGER")
    add_column("payments", "created_at", "DATETIME")

    add_column("expenses", "title", "VARCHAR DEFAULT 'Depense'")
    add_column("expenses", "created_at", "DATETIME")
    add_column("expenses", "updated_at", "DATETIME")
