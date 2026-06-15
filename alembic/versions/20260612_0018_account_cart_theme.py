"""account preferences cart and notification reads

Revision ID: 20260612_0018
Revises: 20260610_0017
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260612_0018"
down_revision = "20260610_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notification_history", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("theme", sa.String(), nullable=False, server_default="light"),
        sa.Column("help_open_mode", sa.String(), nullable=False, server_default="page"),
        sa.Column("email_notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_user_preferences_id", "user_preferences", ["id"])
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True)
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="FCFA"),
        sa.Column("provider_scope", sa.String(), nullable=False, server_default="school"),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    for column in ["id", "user_id", "school_id", "item_type", "provider_scope", "source_type", "source_id"]:
        op.create_index(f"ix_cart_items_{column}", "cart_items", [column])
    op.create_table(
        "school_memberships",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("membership_status", sa.String(), nullable=False, server_default="active"),
        sa.Column("transfer_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    for column in ["id", "user_id", "school_id", "role", "is_active", "membership_status"]:
        op.create_index(f"ix_school_memberships_{column}", "school_memberships", [column])


def downgrade() -> None:
    for column in ["membership_status", "is_active", "role", "school_id", "user_id", "id"]:
        op.drop_index(f"ix_school_memberships_{column}", table_name="school_memberships")
    op.drop_table("school_memberships")
    for column in ["source_id", "source_type", "provider_scope", "item_type", "school_id", "user_id", "id"]:
        op.drop_index(f"ix_cart_items_{column}", table_name="cart_items")
    op.drop_table("cart_items")
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_index("ix_user_preferences_id", table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_column("notification_history", "read_at")
