"""Production readiness secure files.

Revision ID: 20260601_0006
Revises: 20260601_0005
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0006"
down_revision = "20260601_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "secure_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("stored_filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("file_extension", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(), nullable=False),
        sa.Column("storage_backend", sa.String(), nullable=False, server_default="local"),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=True),
        sa.Column("entity_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("scan_status", sa.String(), nullable=False, server_default="not_configured"),
        sa.Column("scan_details", sa.String(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_secure_files_id"), "secure_files", ["id"], unique=False)
    op.create_index(op.f("ix_secure_files_stored_filename"), "secure_files", ["stored_filename"], unique=False)
    op.create_index(op.f("ix_secure_files_file_extension"), "secure_files", ["file_extension"], unique=False)
    op.create_index(op.f("ix_secure_files_checksum_sha256"), "secure_files", ["checksum_sha256"], unique=False)
    op.create_index(op.f("ix_secure_files_entity_type"), "secure_files", ["entity_type"], unique=False)
    op.create_index(op.f("ix_secure_files_entity_id"), "secure_files", ["entity_id"], unique=False)
    op.create_index(op.f("ix_secure_files_status"), "secure_files", ["status"], unique=False)
    op.create_index(op.f("ix_secure_files_scan_status"), "secure_files", ["scan_status"], unique=False)
    op.create_index(op.f("ix_secure_files_school_id"), "secure_files", ["school_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_secure_files_school_id"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_scan_status"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_status"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_entity_id"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_entity_type"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_checksum_sha256"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_file_extension"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_stored_filename"), table_name="secure_files")
    op.drop_index(op.f("ix_secure_files_id"), table_name="secure_files")
    op.drop_table("secure_files")
