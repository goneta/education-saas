"""ai credits and separated payments

Revision ID: 20260609_0015
Revises: 20260609_0014
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "20260609_0015"
down_revision = "20260609_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_providers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("provider_type", sa.String(), nullable=False, index=True),
        sa.Column("api_key_encrypted", sa.String(), nullable=True),
        sa.Column("base_url", sa.String(), nullable=True),
        sa.Column("default_model", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100", index=True),
        sa.Column("cost_per_1k_input_tokens", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost_per_1k_output_tokens", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "ai_credit_packs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("credits_amount", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="FCFA", index=True),
        sa.Column("country_code", sa.String(), nullable=False, server_default="CI", index=True),
        sa.Column("region", sa.String(), nullable=False, server_default="africa", index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("validity_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "ai_wallets",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("owner_type", sa.String(), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
        sa.Column("balance_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_purchased_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_used_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="active", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("owner_type", "user_id", "school_id", name="_ai_wallet_owner_uc"),
    )
    op.create_table(
        "platform_payments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("reference", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("payer_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
        sa.Column("payment_type", sa.String(), nullable=False, index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, index=True),
        sa.Column("country_code", sa.String(), nullable=True, index=True),
        sa.Column("region", sa.String(), nullable=True, index=True),
        sa.Column("provider", sa.String(), nullable=False, index=True),
        sa.Column("provider_reference", sa.String(), nullable=True, index=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending", index=True),
        sa.Column("beneficiary_entity", sa.String(), nullable=False, index=True),
        sa.Column("pack_id", sa.Integer(), sa.ForeignKey("ai_credit_packs.id"), nullable=True),
        sa.Column("credits_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wallet_id", sa.Integer(), sa.ForeignKey("ai_wallets.id"), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
        sa.Column("wallet_id", sa.Integer(), sa.ForeignKey("ai_wallets.id"), nullable=True, index=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("ai_providers.id"), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True, index=True),
        sa.Column("module_name", sa.String(), nullable=True, index=True),
        sa.Column("action_type", sa.String(), nullable=True, index=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_charged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
        sa.Column("request_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="successful", index=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "ai_credit_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("wallet_id", sa.Integer(), sa.ForeignKey("ai_wallets.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
        sa.Column("transaction_type", sa.String(), nullable=False, index=True),
        sa.Column("credits_amount", sa.Integer(), nullable=False),
        sa.Column("balance_before", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("platform_payments.id"), nullable=True, index=True),
        sa.Column("usage_log_id", sa.Integer(), sa.ForeignKey("ai_usage_logs.id"), nullable=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "school_payment_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(), nullable=False, index=True),
        sa.Column("account_name", sa.String(), nullable=False),
        sa.Column("merchant_id", sa.String(), nullable=True),
        sa.Column("api_key_encrypted", sa.String(), nullable=True),
        sa.Column("secret_key_encrypted", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("country_code", sa.String(), nullable=False, server_default="CI", index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "school_payments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("reference", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("payer_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True, index=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("student_invoices.id"), nullable=True, index=True),
        sa.Column("payment_type", sa.String(), nullable=False, index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, index=True),
        sa.Column("provider", sa.String(), nullable=False, index=True),
        sa.Column("provider_reference", sa.String(), nullable=True, index=True),
        sa.Column("school_beneficiary_account_id", sa.Integer(), sa.ForeignKey("school_payment_accounts.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending", index=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    provider_table = sa.table(
        "ai_providers",
        sa.column("name", sa.String()),
        sa.column("provider_type", sa.String()),
        sa.column("default_model", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("priority", sa.Integer()),
        sa.column("currency", sa.String()),
    )
    pack_table = sa.table(
        "ai_credit_packs",
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("credits_amount", sa.Integer()),
        sa.column("price", sa.Float()),
        sa.column("currency", sa.String()),
        sa.column("country_code", sa.String()),
        sa.column("region", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("validity_days", sa.Integer()),
    )
    op.bulk_insert(provider_table, [
        {"name": "OpenAI", "provider_type": "openai", "default_model": "gpt-4.1-mini", "is_active": False, "priority": 10, "currency": "USD"},
    ])
    op.bulk_insert(pack_table, [
        {"name": "Starter IA FCFA", "description": "Pack decouverte IA", "credits_amount": 1500, "price": 7000, "currency": "FCFA", "country_code": "CI", "region": "africa", "is_active": True, "validity_days": 365},
        {"name": "Standard IA FCFA", "description": "Pack standard IA", "credits_amount": 4000, "price": 15000, "currency": "FCFA", "country_code": "CI", "region": "africa", "is_active": True, "validity_days": 365},
        {"name": "Premium IA FCFA", "description": "Pack intensif IA", "credits_amount": 10000, "price": 35000, "currency": "FCFA", "country_code": "CI", "region": "africa", "is_active": True, "validity_days": 365},
        {"name": "Starter AI GBP", "description": "UK AI starter pack", "credits_amount": 1500, "price": 10, "currency": "GBP", "country_code": "GB", "region": "uk_europe", "is_active": True, "validity_days": 365},
        {"name": "Starter AI EUR", "description": "EU AI starter pack", "credits_amount": 1500, "price": 12, "currency": "EUR", "country_code": "FR", "region": "uk_europe", "is_active": True, "validity_days": 365},
    ])


def downgrade() -> None:
    op.drop_table("school_payments")
    op.drop_table("school_payment_accounts")
    op.drop_table("ai_credit_transactions")
    op.drop_table("ai_usage_logs")
    op.drop_table("platform_payments")
    op.drop_table("ai_wallets")
    op.drop_table("ai_credit_packs")
    op.drop_table("ai_providers")
