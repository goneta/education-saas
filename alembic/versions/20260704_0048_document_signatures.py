"""E-signature infrastructure: document_signatures table.

Revision ID: 20260704_0048
Revises: 20260703_0047
Create Date: 2026-07-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260704_0048"
down_revision = "20260703_0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_signatures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("generated_documents.id"), nullable=False),
        sa.Column("signer_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("signer_name", sa.String(), nullable=True),
        sa.Column("signer_role", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("signature", sa.String(), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("document_id", "signer_user_id", name="_document_signer_uc"),
    )
    op.create_index("ix_document_signatures_document_id", "document_signatures", ["document_id"])
    op.create_index("ix_document_signatures_signer_user_id", "document_signatures", ["signer_user_id"])


def downgrade() -> None:
    op.drop_index("ix_document_signatures_signer_user_id", table_name="document_signatures")
    op.drop_index("ix_document_signatures_document_id", table_name="document_signatures")
    op.drop_table("document_signatures")
