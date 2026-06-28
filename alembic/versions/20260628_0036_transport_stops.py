"""Smart Transport: first-class bus stops (GPS + ETA).

Revision ID: 20260628_0036
Revises: 20260628_0035
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0036"
down_revision = "20260628_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transport_stops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("radius_m", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("scheduled_arrival", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["route_id"], ["transport_routes.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transport_stops_route_id"), "transport_stops", ["route_id"], unique=False)
    op.create_index(op.f("ix_transport_stops_school_id"), "transport_stops", ["school_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transport_stops_school_id"), table_name="transport_stops")
    op.drop_index(op.f("ix_transport_stops_route_id"), table_name="transport_stops")
    op.drop_table("transport_stops")
