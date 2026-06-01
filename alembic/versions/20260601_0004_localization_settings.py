"""International localization settings.

Revision ID: 20260601_0004
Revises: 20260601_0003
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0004"
down_revision = "20260601_0003"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("schools") as batch:
        batch.add_column(sa.Column("country_code", sa.String(), nullable=False, server_default="CI"))
        batch.add_column(sa.Column("default_currency", sa.String(), nullable=False, server_default="FCFA"))
        batch.add_column(sa.Column("currency_code", sa.String(), nullable=False, server_default="XOF"))
        batch.add_column(sa.Column("primary_language", sa.String(), nullable=False, server_default="fr"))
        batch.add_column(sa.Column("timezone", sa.String(), nullable=False, server_default="Africa/Abidjan"))
        batch.add_column(sa.Column("date_format", sa.String(), nullable=False, server_default="dd/MM/yyyy"))
        batch.add_column(sa.Column("time_format", sa.String(), nullable=False, server_default="HH:mm"))
        batch.add_column(sa.Column("address_structured", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("formatted_address", sa.String(), nullable=True))
        batch.add_column(sa.Column("phone_country_code", sa.String(), nullable=True))
        batch.add_column(sa.Column("phone_e164", sa.String(), nullable=True))

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("phone_country_code", sa.String(), nullable=True))
        batch.add_column(sa.Column("phone_e164", sa.String(), nullable=True))
        batch.add_column(sa.Column("address_structured", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("formatted_address", sa.String(), nullable=True))

    with op.batch_alter_table("student_profiles") as batch:
        batch.add_column(sa.Column("student_address_structured", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("student_formatted_address", sa.String(), nullable=True))
        batch.add_column(sa.Column("parent_phone_country_code", sa.String(), nullable=True))
        batch.add_column(sa.Column("parent_phone_e164", sa.String(), nullable=True))
        batch.add_column(sa.Column("parent_address_structured", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("parent_formatted_address", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("student_profiles") as batch:
        batch.drop_column("parent_formatted_address")
        batch.drop_column("parent_address_structured")
        batch.drop_column("parent_phone_e164")
        batch.drop_column("parent_phone_country_code")
        batch.drop_column("student_formatted_address")
        batch.drop_column("student_address_structured")

    with op.batch_alter_table("users") as batch:
        batch.drop_column("formatted_address")
        batch.drop_column("address_structured")
        batch.drop_column("phone_e164")
        batch.drop_column("phone_country_code")

    with op.batch_alter_table("schools") as batch:
        batch.drop_column("phone_e164")
        batch.drop_column("phone_country_code")
        batch.drop_column("formatted_address")
        batch.drop_column("address_structured")
        batch.drop_column("time_format")
        batch.drop_column("date_format")
        batch.drop_column("timezone")
        batch.drop_column("primary_language")
        batch.drop_column("currency_code")
        batch.drop_column("default_currency")
        batch.drop_column("country_code")
