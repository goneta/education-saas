"""Initial schema from SQLAlchemy models.

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01
"""

from alembic import op
from backend.database import Base
from backend import models  # noqa: F401

revision = "20260601_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
