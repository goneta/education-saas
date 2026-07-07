"""Enterprise Billing module: config tables.

Creates the *configuration* tables the unified Billing module layers on top of
the existing money infrastructure (school_subscriptions, ai_wallets,
platform_payments, ai_credit_transactions, audit_logs). No money data is
duplicated. New tables only, with inline column FKs (create_table is fine on
SQLite — the "no ALTER of constraints" limit only bites when adding a FK to an
existing table). Idempotent: each table is skipped if it already exists.

Revision ID: 20260707_0051
Revises: 20260705_0050
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260707_0051"
down_revision = "20260705_0050"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("billing_preferences"):
        op.create_table(
            "billing_preferences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("currency", sa.String(), nullable=False, server_default="FCFA"),
            sa.Column("timezone", sa.String(), nullable=True),
            sa.Column("invoice_language", sa.String(), nullable=False, server_default="fr"),
            sa.Column("email_invoices", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("payment_reminders", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("renewal_reminders", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("invoice_recipients", sa.JSON(), nullable=True),
            sa.Column("notification_channels", sa.JSON(), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_billing_preferences_school_id", "billing_preferences", ["school_id"], unique=True)

    if not _has_table("billing_tax_profiles"):
        op.create_table(
            "billing_tax_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("tax_type", sa.String(), nullable=False, server_default="vat"),
            sa.Column("tax_id", sa.String(), nullable=True),
            sa.Column("business_number", sa.String(), nullable=True),
            sa.Column("company_registration", sa.String(), nullable=True),
            sa.Column("legal_name", sa.String(), nullable=True),
            sa.Column("tax_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("tax_exempt", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("billing_address", sa.JSON(), nullable=True),
            sa.Column("shipping_address", sa.JSON(), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_billing_tax_profiles_school_id", "billing_tax_profiles", ["school_id"], unique=True)

    if not _has_table("wallet_auto_recharges"):
        op.create_table(
            "wallet_auto_recharges",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("wallet_id", sa.Integer(), sa.ForeignKey("ai_wallets.id"), nullable=False),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("threshold_credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recharge_credits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recharge_amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(), nullable=True),
            sa.Column("monthly_max_amount", sa.Float(), nullable=True),
            sa.Column("pack_id", sa.Integer(), sa.ForeignKey("ai_credit_packs.id"), nullable=True),
            sa.Column("payment_provider", sa.String(), nullable=True),
            sa.Column("month_anchor", sa.String(), nullable=True),
            sa.Column("month_spent_amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("last_recharge_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_wallet_auto_recharges_wallet_id", "wallet_auto_recharges", ["wallet_id"], unique=True)
        op.create_index("ix_wallet_auto_recharges_school_id", "wallet_auto_recharges", ["school_id"])

    if not _has_table("billing_promo_codes"):
        op.create_table(
            "billing_promo_codes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("kind", sa.String(), nullable=False, server_default="coupon"),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("discount_type", sa.String(), nullable=False, server_default="percent"),
            sa.Column("discount_value", sa.Float(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(), nullable=True),
            sa.Column("applies_to", sa.String(), nullable=False, server_default="any"),
            sa.Column("max_redemptions", sa.Integer(), nullable=True),
            sa.Column("per_school_limit", sa.Integer(), nullable=True, server_default="1"),
            sa.Column("redeemed_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_billing_promo_codes_code", "billing_promo_codes", ["code"], unique=True)
        op.create_index("ix_billing_promo_codes_is_active", "billing_promo_codes", ["is_active"])

    if not _has_table("billing_promo_redemptions"):
        op.create_table(
            "billing_promo_redemptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("promo_id", sa.Integer(), sa.ForeignKey("billing_promo_codes.id"), nullable=False),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("context", sa.String(), nullable=True),
            sa.Column("amount_discounted", sa.Float(), nullable=False, server_default="0"),
            sa.Column("credits_granted", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_billing_promo_redemptions_promo_id", "billing_promo_redemptions", ["promo_id"])
        op.create_index("ix_billing_promo_redemptions_school_id", "billing_promo_redemptions", ["school_id"])


def downgrade() -> None:
    for table in (
        "billing_promo_redemptions",
        "billing_promo_codes",
        "wallet_auto_recharges",
        "billing_tax_profiles",
        "billing_preferences",
    ):
        if _has_table(table):
            op.drop_table(table)
