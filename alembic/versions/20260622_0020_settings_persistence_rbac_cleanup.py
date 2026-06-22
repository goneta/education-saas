"""settings persistence, subscriptions, and RBAC cleanup

Revision ID: 20260622_0020
Revises: 20260621_0019
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260622_0020"
down_revision = "20260621_0019"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table: str, column: str) -> bool:
    return _has_table(table) and column in {row["name"] for row in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if not _has_column("users", "deleted_at"):
        op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    if not _has_table("school_subscriptions"):
        op.create_table(
            "school_subscriptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("plan", sa.String(), nullable=False, server_default="free"),
            sa.Column("billing_cycle", sa.String(), nullable=False, server_default="monthly"),
            sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(), nullable=False, server_default="FCFA"),
            sa.Column("status", sa.String(), nullable=False, server_default="active"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_renewal_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("payment_provider", sa.String(), nullable=True),
            sa.Column("payment_reference", sa.String(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_school_subscriptions_school_id", "school_subscriptions", ["school_id"])
        op.create_index("ix_school_subscriptions_plan", "school_subscriptions", ["plan"])
        op.create_index("ix_school_subscriptions_status", "school_subscriptions", ["status"])
        op.create_index("ix_school_subscriptions_payment_reference", "school_subscriptions", ["payment_reference"])

    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            DELETE FROM role_definitions target
            USING role_definitions keeper
            WHERE target.school_id IS NULL
              AND keeper.school_id IS NULL
              AND target.key = keeper.key
              AND target.id > keeper.id
        """)
        op.execute("""
            DELETE FROM role_definitions scoped
            USING role_definitions global_role
            WHERE scoped.school_id IS NOT NULL
              AND scoped.is_system = TRUE
              AND global_role.school_id IS NULL
              AND global_role.key = scoped.key
        """)
        op.execute("""
            UPDATE role_permission_matrix target
            SET is_enabled = source.any_enabled
            FROM (
                SELECT MIN(id) AS keeper_id, role_key, permission, BOOL_OR(is_enabled) AS any_enabled
                FROM role_permission_matrix
                WHERE school_id IS NULL
                GROUP BY role_key, permission
            ) source
            WHERE target.id = source.keeper_id
        """)
        op.execute("""
            DELETE FROM role_permission_matrix target
            USING role_permission_matrix keeper
            WHERE target.school_id IS NULL
              AND keeper.school_id IS NULL
              AND target.role_key = keeper.role_key
              AND target.permission = keeper.permission
              AND target.id > keeper.id
        """)
        op.execute("""
            DELETE FROM user_role_assignments target
            USING user_role_assignments keeper
            WHERE target.school_id IS NULL
              AND keeper.school_id IS NULL
              AND target.user_id = keeper.user_id
              AND target.role_key = keeper.role_key
              AND target.id > keeper.id
        """)
        op.execute("""
            DELETE FROM role_permissions target
            USING role_permissions keeper
            WHERE target.school_id IS NULL
              AND keeper.school_id IS NULL
              AND target.role = keeper.role
              AND target.permission = keeper.permission
              AND target.id > keeper.id
        """)
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_role_definitions_global_key ON role_definitions (key) WHERE school_id IS NULL")
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_role_permission_matrix_global ON role_permission_matrix (role_key, permission) WHERE school_id IS NULL")
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_role_assignments_global ON user_role_assignments (user_id, role_key) WHERE school_id IS NULL")
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_role_permissions_global ON role_permissions (role, permission) WHERE school_id IS NULL")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS uq_role_permissions_global")
        op.execute("DROP INDEX IF EXISTS uq_user_role_assignments_global")
        op.execute("DROP INDEX IF EXISTS uq_role_permission_matrix_global")
        op.execute("DROP INDEX IF EXISTS uq_role_definitions_global_key")
    if _has_table("school_subscriptions"):
        op.drop_table("school_subscriptions")
    if _has_column("users", "deleted_at"):
        op.drop_index("ix_users_deleted_at", table_name="users")
        op.drop_column("users", "deleted_at")
