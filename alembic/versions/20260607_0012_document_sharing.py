"""document sharing module

Revision ID: 20260607_0012
Revises: 20260607_0011
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260607_0012"
down_revision = "20260607_0011"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _has_foreign_key(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {foreign_key.get("name") for foreign_key in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    if not _has_column("users", "numref"):
        op.add_column("users", sa.Column("numref", sa.String(), nullable=True))
    connection = op.get_bind()
    for row in connection.execute(sa.text("SELECT id FROM users WHERE numref IS NULL")).mappings():
        connection.execute(
            sa.text("UPDATE users SET numref = :numref WHERE id = :id"),
            {"numref": f"USR-2026-{int(row['id']):06d}", "id": row["id"]},
        )
    if not _has_index("users", "ix_users_numref"):
        op.create_index("ix_users_numref", "users", ["numref"], unique=True)
    secure_file_columns = {
        "display_name": sa.Column("display_name", sa.String(), nullable=True),
        "category": sa.Column("category", sa.String(), nullable=True),
        "visibility": sa.Column("visibility", sa.String(), nullable=False, server_default="private"),
        "is_shareable": sa.Column("is_shareable", sa.Boolean(), nullable=False, server_default=sa.false()),
        "approval_status": sa.Column("approval_status", sa.String(), nullable=False, server_default="approved"),
        "approved_by_id": sa.Column("approved_by_id", sa.Integer(), nullable=True),
        "approved_at": sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        "expires_at": sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        "download_limit": sa.Column("download_limit", sa.Integer(), nullable=True),
        "access_count": sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
    }
    for column_name, column in secure_file_columns.items():
        if not _has_column("secure_files", column_name):
            op.add_column("secure_files", column)
    for index_name, column_name in {
        "ix_secure_files_display_name": "display_name",
        "ix_secure_files_category": "category",
        "ix_secure_files_visibility": "visibility",
        "ix_secure_files_approval_status": "approval_status",
    }.items():
        if not _has_index("secure_files", index_name):
            op.create_index(index_name, "secure_files", [column_name])
    if not _has_foreign_key("secure_files", "fk_secure_files_approved_by_id_users"):
        with op.batch_alter_table("secure_files") as batch_op:
            batch_op.create_foreign_key("fk_secure_files_approved_by_id_users", "users", ["approved_by_id"], ["id"])
    if not _has_table("document_shares"):
        op.create_table(
            "document_shares",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("file_id", sa.Integer(), sa.ForeignKey("secure_files.id"), nullable=False, index=True),
            sa.Column("share_type", sa.String(), nullable=False, index=True),
            sa.Column("mode", sa.String(), nullable=False, server_default="private", index=True),
            sa.Column("can_reshare", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
            sa.Column("recipient_school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
            sa.Column("recipient_numref", sa.String(), nullable=True, index=True),
            sa.Column("status", sa.String(), nullable=False, server_default="active", index=True),
            sa.Column("encrypted_token", sa.String(), nullable=False, unique=True, index=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("download_limit", sa.Integer(), nullable=True),
            sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("document_shares")
    with op.batch_alter_table("secure_files") as batch_op:
        batch_op.drop_constraint("fk_secure_files_approved_by_id_users", type_="foreignkey")
    op.drop_index("ix_secure_files_approval_status", table_name="secure_files")
    op.drop_index("ix_secure_files_visibility", table_name="secure_files")
    op.drop_index("ix_secure_files_category", table_name="secure_files")
    op.drop_index("ix_secure_files_display_name", table_name="secure_files")
    for column in ["access_count", "download_limit", "expires_at", "approved_at", "approved_by_id", "approval_status", "is_shareable", "visibility", "category", "display_name"]:
        op.drop_column("secure_files", column)
    op.drop_index("ix_users_numref", table_name="users")
    op.drop_column("users", "numref")
