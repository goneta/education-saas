"""Enterprise production controls.

Revision ID: 20260601_0007
Revises: 20260601_0006
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0007"
down_revision = "20260601_0006"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("schools") as batch:
        batch.add_column(sa.Column("subscription_status", sa.String(), nullable=False, server_default="active"))
        batch.add_column(sa.Column("storage_quota_mb", sa.Integer(), nullable=False, server_default="1024"))
        batch.add_column(sa.Column("current_billing_period_end", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("notification_messages") as batch:
        batch.add_column(sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("template_key", sa.String(), nullable=True))
        batch.add_column(sa.Column("locale", sa.String(), nullable=False, server_default="fr"))
    op.create_index(op.f("ix_notification_messages_template_key"), "notification_messages", ["template_key"], unique=False)

    op.create_table(
        "data_consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject_user_id", sa.Integer(), nullable=False),
        sa.Column("consent_type", sa.String(), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("locale", sa.String(), nullable=False, server_default="fr"),
        sa.Column("policy_version", sa.String(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("recorded_by_id", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_consents_id"), "data_consents", ["id"], unique=False)
    op.create_index(op.f("ix_data_consents_subject_user_id"), "data_consents", ["subject_user_id"], unique=False)
    op.create_index(op.f("ix_data_consents_consent_type"), "data_consents", ["consent_type"], unique=False)
    op.create_index(op.f("ix_data_consents_school_id"), "data_consents", ["school_id"], unique=False)

    op.create_table(
        "data_retention_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data_category", sa.String(), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("legal_basis", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False, server_default="review"),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_retention_rules_id"), "data_retention_rules", ["id"], unique=False)
    op.create_index(op.f("ix_data_retention_rules_data_category"), "data_retention_rules", ["data_category"], unique=False)
    op.create_index(op.f("ix_data_retention_rules_school_id"), "data_retention_rules", ["school_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_data_retention_rules_school_id"), table_name="data_retention_rules")
    op.drop_index(op.f("ix_data_retention_rules_data_category"), table_name="data_retention_rules")
    op.drop_index(op.f("ix_data_retention_rules_id"), table_name="data_retention_rules")
    op.drop_table("data_retention_rules")
    op.drop_index(op.f("ix_data_consents_school_id"), table_name="data_consents")
    op.drop_index(op.f("ix_data_consents_consent_type"), table_name="data_consents")
    op.drop_index(op.f("ix_data_consents_subject_user_id"), table_name="data_consents")
    op.drop_index(op.f("ix_data_consents_id"), table_name="data_consents")
    op.drop_table("data_consents")
    op.drop_index(op.f("ix_notification_messages_template_key"), table_name="notification_messages")
    with op.batch_alter_table("notification_messages") as batch:
        batch.drop_column("locale")
        batch.drop_column("template_key")
        batch.drop_column("next_retry_at")
        batch.drop_column("attempts")
    with op.batch_alter_table("schools") as batch:
        batch.drop_column("current_billing_period_end")
        batch.drop_column("storage_quota_mb")
        batch.drop_column("subscription_status")
