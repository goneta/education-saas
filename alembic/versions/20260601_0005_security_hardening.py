"""Security hardening fields and events.

Revision ID: 20260601_0005
Revises: 20260601_0004
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0005"
down_revision = "20260601_0004"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("mfa_secret", sa.String(), nullable=True))
        batch.add_column(sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False, server_default="info"),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_events_id"), "security_events", ["id"], unique=False)
    op.create_index(op.f("ix_security_events_event_type"), "security_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_security_events_severity"), "security_events", ["severity"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_security_events_severity"), table_name="security_events")
    op.drop_index(op.f("ix_security_events_event_type"), table_name="security_events")
    op.drop_index(op.f("ix_security_events_id"), table_name="security_events")
    op.drop_table("security_events")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("token_version")
        batch.drop_column("last_login_at")
        batch.drop_column("locked_until")
        batch.drop_column("failed_login_attempts")
        batch.drop_column("mfa_secret")
        batch.drop_column("mfa_enabled")
