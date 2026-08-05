"""Self-service password reset + TOTP anti-replay (audit SEC-05 / SEC-04).

Creates `password_reset_tokens` (hashed one-shot tokens with expiry) and adds
`users.mfa_last_code` so an accepted TOTP cannot be presented twice inside its
validity window. New table + column only, inline column FK, idempotent.

Revision ID: 20260805_0057
Revises: 20260805_0056
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260805_0057"
down_revision = "20260805_0056"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def upgrade() -> None:
    inspector = _inspector()
    if "password_reset_tokens" not in inspector.get_table_names():
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_hash", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("requested_ip", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
        op.create_index(
            "ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True
        )

    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "mfa_last_code" not in columns:
            op.add_column("users", sa.Column("mfa_last_code", sa.String(), nullable=True))


def downgrade() -> None:
    inspector = _inspector()
    if "password_reset_tokens" in inspector.get_table_names():
        op.drop_table("password_reset_tokens")
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "mfa_last_code" in columns:
            op.drop_column("users", "mfa_last_code")
