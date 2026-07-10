"""Diploma / certificate template module.

Creates document_templates: per-school (multi-tenant) templates for diplomas
and certificates — optional uploaded background, {{placeholder}} title/body,
extensible fields_config, one default per (school, kind). New table only,
inline column FKs, idempotent.

Revision ID: 20260708_0054
Revises: 20260708_0053
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260708_0054"
down_revision = "20260708_0053"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_table("document_templates"):
        op.create_table(
            "document_templates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("title_text", sa.String(), nullable=True),
            sa.Column("body_text", sa.Text(), nullable=True),
            sa.Column("background_path", sa.String(), nullable=True),
            sa.Column("background_type", sa.String(), nullable=True),
            sa.Column("background_filename", sa.String(), nullable=True),
            sa.Column("fields_config", sa.JSON(), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_document_templates_school_id", "document_templates", ["school_id"])
        op.create_index("ix_document_templates_kind", "document_templates", ["kind"])
        op.create_index("ix_document_templates_is_default", "document_templates", ["is_default"])
        op.create_index("ix_document_templates_is_active", "document_templates", ["is_active"])


def downgrade() -> None:
    if _has_table("document_templates"):
        op.drop_table("document_templates")
