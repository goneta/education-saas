"""ai provider catalog and wallet limits

Revision ID: 20260610_0016
Revises: 20260609_0015
Create Date: 2026-06-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260610_0016"
down_revision = "20260609_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_wallets", sa.Column("daily_credit_limit", sa.Integer(), nullable=True))
    op.add_column("ai_wallets", sa.Column("monthly_credit_limit", sa.Integer(), nullable=True))

    provider_table = sa.table(
        "ai_providers",
        sa.column("name", sa.String()),
        sa.column("provider_type", sa.String()),
        sa.column("base_url", sa.String()),
        sa.column("default_model", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("priority", sa.Integer()),
        sa.column("cost_per_1k_input_tokens", sa.Float()),
        sa.column("cost_per_1k_output_tokens", sa.Float()),
        sa.column("currency", sa.String()),
    )
    op.bulk_insert(provider_table, [
        {"name": "Claude", "provider_type": "anthropic", "base_url": None, "default_model": "claude-3-5-sonnet-latest", "is_active": False, "priority": 20, "cost_per_1k_input_tokens": 0, "cost_per_1k_output_tokens": 0, "currency": "USD"},
        {"name": "Gemini", "provider_type": "gemini", "base_url": None, "default_model": "gemini-1.5-pro", "is_active": False, "priority": 30, "cost_per_1k_input_tokens": 0, "cost_per_1k_output_tokens": 0, "currency": "USD"},
        {"name": "OpenRouter", "provider_type": "openrouter", "base_url": "https://openrouter.ai/api/v1", "default_model": "openai/gpt-4o-mini", "is_active": False, "priority": 40, "cost_per_1k_input_tokens": 0, "cost_per_1k_output_tokens": 0, "currency": "USD"},
        {"name": "Grok", "provider_type": "grok", "base_url": "https://api.x.ai/v1", "default_model": "grok-2-latest", "is_active": False, "priority": 50, "cost_per_1k_input_tokens": 0, "cost_per_1k_output_tokens": 0, "currency": "USD"},
        {"name": "Manus", "provider_type": "manus", "base_url": None, "default_model": "manus-default", "is_active": False, "priority": 60, "cost_per_1k_input_tokens": 0, "cost_per_1k_output_tokens": 0, "currency": "USD"},
        {"name": "Custom API", "provider_type": "custom", "base_url": None, "default_model": "custom-model", "is_active": False, "priority": 100, "cost_per_1k_input_tokens": 0, "cost_per_1k_output_tokens": 0, "currency": "USD"},
    ])


def downgrade() -> None:
    op.execute("DELETE FROM ai_providers WHERE provider_type IN ('anthropic', 'gemini', 'openrouter', 'grok', 'manus', 'custom')")
    op.drop_column("ai_wallets", "monthly_credit_limit")
    op.drop_column("ai_wallets", "daily_credit_limit")
