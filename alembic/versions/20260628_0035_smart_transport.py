"""Smart Transport: driver + vehicle master data and route links.

Revision ID: 20260628_0035
Revises: 20260628_0034
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0035"
down_revision = "20260628_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transport_drivers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("license_number", sa.String(), nullable=True),
        sa.Column("license_expiry", sa.DateTime(), nullable=True),
        sa.Column("employment_status", sa.String(), nullable=False, server_default="active"),
        sa.Column("medical_clearance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transport_drivers_school_id"), "transport_drivers", ["school_id"], unique=False)
    op.create_index(op.f("ix_transport_drivers_full_name"), "transport_drivers", ["full_name"], unique=False)

    op.create_table(
        "transport_vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("vehicle_type", sa.String(), nullable=False, server_default="bus"),
        sa.Column("registration", sa.String(), nullable=True),
        sa.Column("vin", sa.String(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("insurance_expiry", sa.DateTime(), nullable=True),
        sa.Column("mileage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="operational"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transport_vehicles_school_id"), "transport_vehicles", ["school_id"], unique=False)
    op.create_index(op.f("ix_transport_vehicles_name"), "transport_vehicles", ["name"], unique=False)

    # Column-only links on the existing routes table: SQLite cannot ALTER TABLE
    # ADD CONSTRAINT, so the FKs are declared on the ORM model.
    op.add_column("transport_routes", sa.Column("driver_id", sa.Integer(), nullable=True))
    op.add_column("transport_routes", sa.Column("vehicle_id", sa.Integer(), nullable=True))
    op.add_column("transport_routes", sa.Column("capacity", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("transport_routes", "capacity")
    op.drop_column("transport_routes", "vehicle_id")
    op.drop_column("transport_routes", "driver_id")
    op.drop_index(op.f("ix_transport_vehicles_name"), table_name="transport_vehicles")
    op.drop_index(op.f("ix_transport_vehicles_school_id"), table_name="transport_vehicles")
    op.drop_table("transport_vehicles")
    op.drop_index(op.f("ix_transport_drivers_full_name"), table_name="transport_drivers")
    op.drop_index(op.f("ix_transport_drivers_school_id"), table_name="transport_drivers")
    op.drop_table("transport_drivers")
