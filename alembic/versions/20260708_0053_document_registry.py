"""Universal document authenticity registry.

Creates document_registry: a UUID-keyed authenticity record for every generated
document (invoice, report card, certificate, diploma, payslip, ...). References
the source record (source_type/source_id), never duplicates it. New table only,
inline column FKs, idempotent.

Revision ID: 20260708_0053
Revises: 20260707_0052
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260708_0053"
down_revision = "20260707_0052"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("document_registry"):
        op.create_table(
            "document_registry",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("uuid", sa.String(), nullable=False),
            sa.Column("document_type", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column("reference", sa.String(), nullable=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
            sa.Column("issued_to_name", sa.String(), nullable=True),
            sa.Column("issued_to_id", sa.Integer(), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("content_hash", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="valid"),
            sa.Column("source_type", sa.String(), nullable=True),
            sa.Column("source_id", sa.Integer(), nullable=True),
            sa.Column("issued_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("source_type", "source_id", name="_document_registry_source_uc"),
        )
        op.create_index("ix_document_registry_uuid", "document_registry", ["uuid"], unique=True)
        op.create_index("ix_document_registry_document_type", "document_registry", ["document_type"])
        op.create_index("ix_document_registry_school_id", "document_registry", ["school_id"])
        op.create_index("ix_document_registry_reference", "document_registry", ["reference"])
        op.create_index("ix_document_registry_status", "document_registry", ["status"])
        op.create_index("ix_document_registry_source_id", "document_registry", ["source_id"])


def downgrade() -> None:
    if _has_table("document_registry"):
        op.drop_table("document_registry")
