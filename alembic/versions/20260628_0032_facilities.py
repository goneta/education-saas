"""Facilities: campuses, buildings, rooms, equipment + timetable room link.

Revision ID: 20260628_0032
Revises: 20260627_0031
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0032"
down_revision = "20260627_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campuses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_campuses_school_id"), "campuses", ["school_id"], unique=False)

    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("campus_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_buildings_school_id"), "buildings", ["school_id"], unique=False)
    op.create_index(op.f("ix_buildings_campus_id"), "buildings", ["campus_id"], unique=False)

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("room_type", sa.String(), nullable=False, server_default="classroom"),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_school_id"), "rooms", ["school_id"], unique=False)
    op.create_index(op.f("ix_rooms_building_id"), "rooms", ["building_id"], unique=False)
    op.create_index(op.f("ix_rooms_is_active"), "rooms", ["is_active"], unique=False)

    op.create_table(
        "room_equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_equipment_room_id"), "room_equipment", ["room_id"], unique=False)

    # Column + index only: SQLite cannot ALTER TABLE ADD CONSTRAINT, so the
    # FK is declared on the ORM model rather than as a standalone DB constraint.
    op.add_column("timetables", sa.Column("room_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_timetables_room_id"), "timetables", ["room_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_timetables_room_id"), table_name="timetables")
    op.drop_column("timetables", "room_id")
    op.drop_index(op.f("ix_room_equipment_room_id"), table_name="room_equipment")
    op.drop_table("room_equipment")
    op.drop_index(op.f("ix_rooms_is_active"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_building_id"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_school_id"), table_name="rooms")
    op.drop_table("rooms")
    op.drop_index(op.f("ix_buildings_campus_id"), table_name="buildings")
    op.drop_index(op.f("ix_buildings_school_id"), table_name="buildings")
    op.drop_table("buildings")
    op.drop_index(op.f("ix_campuses_school_id"), table_name="campuses")
    op.drop_table("campuses")
