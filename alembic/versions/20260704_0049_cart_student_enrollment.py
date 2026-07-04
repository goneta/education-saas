"""Repair: cart_items.student_enrollment_id existed on the model but was never
migrated.

The CartItem model gained `student_enrollment_id` (historisation link) without
a matching migration; SQLite dev databases built via `Base.metadata.create_all`
had the column, but Postgres production databases built via alembic did not —
every `GET /account/cart` failed with `psycopg2.errors.UndefinedColumn`.
A schema diff (alembic-built vs model-built) confirms this was the ONLY drift.

Revision ID: 20260704_0049
Revises: 20260704_0048
Create Date: 2026-07-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260704_0049"
down_revision = "20260704_0048"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    # Idempotent: dev databases created from the models already carry the column.
    if not _has_column("cart_items", "student_enrollment_id"):
        op.add_column("cart_items", sa.Column("student_enrollment_id", sa.Integer(), nullable=True))
        op.create_index("ix_cart_items_student_enrollment_id", "cart_items", ["student_enrollment_id"])


def downgrade() -> None:
    if _has_column("cart_items", "student_enrollment_id"):
        op.drop_index("ix_cart_items_student_enrollment_id", table_name="cart_items")
        op.drop_column("cart_items", "student_enrollment_id")
