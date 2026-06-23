"""AI credit monitoring settings."""

from alembic import op
import sqlalchemy as sa


revision = "20260623_0025"
down_revision = "20260623_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_providers", sa.Column("account_label", sa.String(), nullable=True))
    op.add_column("ai_providers", sa.Column("available_credits", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ai_providers", sa.Column("credits_last_synced_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "platform_ai_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("low_credit_threshold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notification_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_platform_ai_settings_id"), "platform_ai_settings", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_platform_ai_settings_id"), table_name="platform_ai_settings")
    op.drop_table("platform_ai_settings")
    op.drop_column("ai_providers", "credits_last_synced_at")
    op.drop_column("ai_providers", "available_credits")
    op.drop_column("ai_providers", "account_label")
