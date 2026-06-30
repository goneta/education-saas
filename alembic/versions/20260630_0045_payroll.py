"""Payroll: salary_profiles + payroll_records breakdown columns.

Revision ID: 20260630_0045
Revises: 20260630_0044
Create Date: 2026-06-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0045"
down_revision = "20260630_0044"
branch_labels = None
depends_on = None


_NEW_COLUMNS = [
    ("period_type", sa.String()),
    ("pay_type", sa.String()),
    ("currency", sa.String()),
    ("country_code", sa.String()),
    ("base_amount", sa.Float()),
    ("allowances_total", sa.Float()),
    ("bonus_total", sa.Float()),
    ("overtime_total", sa.Float()),
    ("advances_total", sa.Float()),
    ("other_deductions_total", sa.Float()),
    ("social_contributions", sa.Float()),
    ("tax_amount", sa.Float()),
    ("academic_year_id", sa.Integer()),
    ("payment_method", sa.String()),
    ("payment_reference", sa.String()),
]


def upgrade() -> None:
    for name, col_type in _NEW_COLUMNS:
        op.add_column("payroll_records", sa.Column(name, col_type, nullable=True))

    op.create_table(
        "salary_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("employee_type", sa.String(), nullable=False, server_default="permanent"),
        sa.Column("pay_type", sa.String(), nullable=False, server_default="monthly"),
        sa.Column("base_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=False, server_default="XOF"),
        sa.Column("country_code", sa.String(), nullable=True),
        sa.Column("cotisation_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_salary_profiles_user_id", "salary_profiles", ["user_id"], unique=True)
    op.create_index("ix_salary_profiles_school_id", "salary_profiles", ["school_id"])


def downgrade() -> None:
    op.drop_index("ix_salary_profiles_school_id", table_name="salary_profiles")
    op.drop_index("ix_salary_profiles_user_id", table_name="salary_profiles")
    op.drop_table("salary_profiles")
    for name, _ in reversed(_NEW_COLUMNS):
        op.drop_column("payroll_records", name)
