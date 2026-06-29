"""SIS: guardians, emergency contacts, medical records.

Revision ID: 20260629_0039
Revises: 20260629_0038
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260629_0039"
down_revision = "20260629_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_guardians",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("relationship_type", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_pickup", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_student_guardians_student_id"), "student_guardians", ["student_id"], unique=False)

    op.create_table(
        "student_emergency_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("relationship_type", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_student_emergency_contacts_student_id"), "student_emergency_contacts", ["student_id"], unique=False)

    op.create_table(
        "student_medical_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("blood_group", sa.String(), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("chronic_conditions", sa.Text(), nullable=True),
        sa.Column("medications", sa.Text(), nullable=True),
        sa.Column("physician_name", sa.String(), nullable=True),
        sa.Column("physician_phone", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", name="uq_medical_record_student"),
    )
    op.create_index(op.f("ix_student_medical_records_student_id"), "student_medical_records", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_student_medical_records_student_id"), table_name="student_medical_records")
    op.drop_table("student_medical_records")
    op.drop_index(op.f("ix_student_emergency_contacts_student_id"), table_name="student_emergency_contacts")
    op.drop_table("student_emergency_contacts")
    op.drop_index(op.f("ix_student_guardians_student_id"), table_name="student_guardians")
    op.drop_table("student_guardians")
