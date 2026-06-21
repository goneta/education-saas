"""cash payments and school AI credit allocations

Revision ID: 20260621_0019
Revises: 20260612_0018
Create Date: 2026-06-21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260621_0019"
down_revision = "20260612_0018"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return index_name in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    payment_columns = [
        ("payment_method", sa.Column("payment_method", sa.String(), nullable=False, server_default="cash")),
        ("status", sa.Column("status", sa.String(), nullable=False, server_default="successful")),
        ("internal_reference", sa.Column("internal_reference", sa.String(), nullable=True)),
    ]
    for name, column in payment_columns:
        if not _has_column("payments", name):
            op.add_column("payments", column)
    for name in ["payment_method", "status", "internal_reference"]:
        index_name = f"ix_payments_{name}"
        if not _has_index("payments", index_name):
            op.create_index(index_name, "payments", [name])

    if not _has_column("ai_credit_packs", "target_type"):
        op.add_column("ai_credit_packs", sa.Column("target_type", sa.String(), nullable=False, server_default="both"))
    if not _has_index("ai_credit_packs", "ix_ai_credit_packs_target_type"):
        op.create_index("ix_ai_credit_packs_target_type", "ai_credit_packs", ["target_type"])

    if not _has_column("platform_payments", "validated_by_id"):
        if op.get_bind().dialect.name == "sqlite":
            op.add_column("platform_payments", sa.Column("validated_by_id", sa.Integer(), nullable=True))
        else:
            op.add_column("platform_payments", sa.Column("validated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    if not _has_column("platform_payments", "validated_at"):
        op.add_column("platform_payments", sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_index("platform_payments", "ix_platform_payments_validated_by_id"):
        op.create_index("ix_platform_payments_validated_by_id", "platform_payments", ["validated_by_id"])

    if not _has_table("school_ai_credit_allocations"):
        op.create_table(
            "school_ai_credit_allocations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("school_wallet_id", sa.Integer(), sa.ForeignKey("ai_wallets.id"), nullable=False),
            sa.Column("user_wallet_id", sa.Integer(), sa.ForeignKey("ai_wallets.id"), nullable=False),
            sa.Column("allocated_credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("remaining_credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("consumed_credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("granted_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    for column in ["id", "school_id", "user_id", "school_wallet_id", "user_wallet_id", "is_active"]:
        index_name = f"ix_school_ai_credit_allocations_{column}"
        if not _has_index("school_ai_credit_allocations", index_name):
            op.create_index(index_name, "school_ai_credit_allocations", [column])


def downgrade() -> None:
    if _has_table("school_ai_credit_allocations"):
        op.drop_table("school_ai_credit_allocations")
    if _has_index("platform_payments", "ix_platform_payments_validated_by_id"):
        op.drop_index("ix_platform_payments_validated_by_id", table_name="platform_payments")
    for column in ["validated_at", "validated_by_id"]:
        if _has_column("platform_payments", column):
            op.drop_column("platform_payments", column)
    if _has_index("ai_credit_packs", "ix_ai_credit_packs_target_type"):
        op.drop_index("ix_ai_credit_packs_target_type", table_name="ai_credit_packs")
    if _has_column("ai_credit_packs", "target_type"):
        op.drop_column("ai_credit_packs", "target_type")
    for name in ["internal_reference", "status", "payment_method"]:
        index_name = f"ix_payments_{name}"
        if _has_index("payments", index_name):
            op.drop_index(index_name, table_name="payments")
        if _has_column("payments", name):
            op.drop_column("payments", name)
