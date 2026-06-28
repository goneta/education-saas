"""Smart Transport: GPS positions, boarding events, incidents, fuel logs.

Revision ID: 20260628_0037
Revises: 20260628_0036
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0037"
down_revision = "20260628_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transport_vehicle_positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["transport_vehicles.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transport_vehicle_positions_vehicle_id"), "transport_vehicle_positions", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_transport_vehicle_positions_school_id"), "transport_vehicle_positions", ["school_id"], unique=False)
    op.create_index(op.f("ix_transport_vehicle_positions_recorded_at"), "transport_vehicle_positions", ["recorded_at"], unique=False)

    op.create_table(
        "transport_boarding_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=True),
        sa.Column("stop_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(), nullable=False, server_default="morning"),
        sa.Column("event_type", sa.String(), nullable=False, server_default="boarded"),
        sa.Column("method", sa.String(), nullable=False, server_default="manual"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.ForeignKeyConstraint(["route_id"], ["transport_routes.id"]),
        sa.ForeignKeyConstraint(["stop_id"], ["transport_stops.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transport_boarding_events_student_id"), "transport_boarding_events", ["student_id"], unique=False)
    op.create_index(op.f("ix_transport_boarding_events_school_id"), "transport_boarding_events", ["school_id"], unique=False)
    op.create_index(op.f("ix_transport_boarding_events_recorded_at"), "transport_boarding_events", ["recorded_at"], unique=False)

    op.create_table(
        "transport_incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=True),
        sa.Column("route_id", sa.Integer(), nullable=True),
        sa.Column("incident_type", sa.String(), nullable=False, server_default="other"),
        sa.Column("severity", sa.String(), nullable=False, server_default="low"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["transport_vehicles.id"]),
        sa.ForeignKeyConstraint(["route_id"], ["transport_routes.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transport_incidents_school_id"), "transport_incidents", ["school_id"], unique=False)

    op.create_table(
        "transport_fuel_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("liters", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("odometer", sa.Float(), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["transport_vehicles.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transport_fuel_logs_vehicle_id"), "transport_fuel_logs", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_transport_fuel_logs_school_id"), "transport_fuel_logs", ["school_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transport_fuel_logs_school_id"), table_name="transport_fuel_logs")
    op.drop_index(op.f("ix_transport_fuel_logs_vehicle_id"), table_name="transport_fuel_logs")
    op.drop_table("transport_fuel_logs")
    op.drop_index(op.f("ix_transport_incidents_school_id"), table_name="transport_incidents")
    op.drop_table("transport_incidents")
    op.drop_index(op.f("ix_transport_boarding_events_recorded_at"), table_name="transport_boarding_events")
    op.drop_index(op.f("ix_transport_boarding_events_school_id"), table_name="transport_boarding_events")
    op.drop_index(op.f("ix_transport_boarding_events_student_id"), table_name="transport_boarding_events")
    op.drop_table("transport_boarding_events")
    op.drop_index(op.f("ix_transport_vehicle_positions_recorded_at"), table_name="transport_vehicle_positions")
    op.drop_index(op.f("ix_transport_vehicle_positions_school_id"), table_name="transport_vehicle_positions")
    op.drop_index(op.f("ix_transport_vehicle_positions_vehicle_id"), table_name="transport_vehicle_positions")
    op.drop_table("transport_vehicle_positions")
