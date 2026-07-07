"""Billing: saved payment methods table.

Stores only display metadata (brand, last4, expiry) + an optional gateway token
per school — PCI-safe, no PAN/CVV. New table only, inline column FKs, idempotent.

Revision ID: 20260707_0052
Revises: 20260707_0051
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260707_0052"
down_revision = "20260707_0051"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("billing_payment_methods"):
        op.create_table(
            "billing_payment_methods",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("method_type", sa.String(), nullable=False, server_default="card"),
            sa.Column("provider", sa.String(), nullable=False),
            sa.Column("nickname", sa.String(), nullable=True),
            sa.Column("holder_name", sa.String(), nullable=True),
            sa.Column("brand", sa.String(), nullable=True),
            sa.Column("last4", sa.String(), nullable=True),
            sa.Column("expiry_month", sa.Integer(), nullable=True),
            sa.Column("expiry_year", sa.Integer(), nullable=True),
            sa.Column("billing_address", sa.JSON(), nullable=True),
            sa.Column("gateway_token", sa.String(), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("status", sa.String(), nullable=False, server_default="active"),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_billing_payment_methods_school_id", "billing_payment_methods", ["school_id"])
        op.create_index("ix_billing_payment_methods_status", "billing_payment_methods", ["status"])


def downgrade() -> None:
    if _has_table("billing_payment_methods"):
        op.drop_table("billing_payment_methods")
