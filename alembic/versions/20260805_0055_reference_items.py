"""Hierarchical reference data (global TeducAI lists + per-school extensions).

Creates reference_items: one generic table for every referential list —
rows with school_id NULL are GLOBAL (Super-Admin-managed, read-only for
schools), rows with a school_id are LOCAL to that school. Seeds the global
lists (fee/room/building/leave/evaluation/document/sanction/reward/school
types) so schools start with sensible platform data; school levels keep the
existing SchoolLevel referential as their global source (no duplication).
New table only, inline column FKs, idempotent.

Revision ID: 20260805_0055
Revises: 20260708_0054
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260805_0055"
down_revision = "20260708_0054"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in inspector.get_table_names()


GLOBAL_SEEDS: dict[str, list[tuple[str, str]]] = {
    "school_type": [
        ("PRESCHOOL", "Préscolaire / Maternelle"),
        ("PRIMARY", "Primaire"),
        ("SECONDARY_GENERAL", "Secondaire général"),
        ("SECONDARY_TECHNICAL", "Secondaire technique"),
        ("VOCATIONAL", "Formation professionnelle"),
        ("HIGHER_EDUCATION", "Enseignement supérieur"),
    ],
    "fee_type": [
        ("REGISTRATION", "Frais d'inscription"),
        ("TUITION", "Scolarité"),
        ("CANTEEN", "Cantine"),
        ("TRANSPORT", "Transport"),
        ("EXAM", "Frais d'examen"),
        ("UNIFORM", "Uniformes"),
        ("BOOKS", "Livres et fournitures"),
        ("ACTIVITIES", "Activités et sorties"),
    ],
    "room_type": [
        ("CLASSROOM", "Salle de classe"),
        ("LAB", "Laboratoire"),
        ("COMPUTER_ROOM", "Salle informatique"),
        ("LIBRARY", "Bibliothèque"),
        ("GYM", "Gymnase / Sport"),
        ("AUDITORIUM", "Amphithéâtre"),
        ("OFFICE", "Bureau administratif"),
    ],
    "building_type": [
        ("TEACHING", "Bâtiment pédagogique"),
        ("ADMINISTRATION", "Bâtiment administratif"),
        ("DORMITORY", "Internat / Dortoir"),
        ("SPORTS", "Installations sportives"),
        ("CANTEEN", "Cantine / Réfectoire"),
    ],
    "leave_type": [
        ("ANNUAL", "Congé annuel"),
        ("SICK", "Congé maladie"),
        ("MATERNITY", "Congé maternité"),
        ("PATERNITY", "Congé paternité"),
        ("UNPAID", "Congé sans solde"),
        ("EXCEPTIONAL", "Absence exceptionnelle"),
    ],
    "evaluation_type": [
        ("HOMEWORK", "Devoir de maison"),
        ("QUIZ", "Interrogation"),
        ("TEST", "Devoir surveillé"),
        ("EXAM", "Examen"),
        ("ORAL", "Évaluation orale"),
        ("PRACTICAL", "Travaux pratiques"),
    ],
    "document_type": [
        ("CERTIFICATE", "Certificat de scolarité"),
        ("ATTESTATION", "Attestation de fréquentation"),
        ("RECEIPT", "Reçu de paiement"),
        ("REPORT_CARD", "Bulletin de notes"),
        ("DIPLOMA", "Diplôme"),
        ("TRANSCRIPT", "Relevé de notes"),
    ],
    "sanction_type": [
        ("WARNING", "Avertissement"),
        ("REPRIMAND", "Blâme"),
        ("DETENTION", "Retenue"),
        ("SUSPENSION", "Exclusion temporaire"),
        ("EXPULSION", "Exclusion définitive"),
    ],
    "reward_type": [
        ("HONOR_ROLL", "Tableau d'honneur"),
        ("CONGRATULATIONS", "Félicitations"),
        ("ENCOURAGEMENT", "Encouragements"),
        ("PRIZE", "Prix d'excellence"),
    ],
}


def upgrade() -> None:
    if not _has_table("reference_items"):
        op.create_table(
            "reference_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("category", "code", "school_id", name="_reference_item_uc"),
        )
        op.create_index("ix_reference_items_category", "reference_items", ["category"])
        op.create_index("ix_reference_items_code", "reference_items", ["code"])
        op.create_index("ix_reference_items_school_id", "reference_items", ["school_id"])
        op.create_index("ix_reference_items_is_active", "reference_items", ["is_active"])

    # Seed the GLOBAL lists (idempotent: skip codes already present).
    bind = op.get_bind()
    existing = {
        (row[0], row[1])
        for row in bind.execute(sa.text(
            "SELECT category, code FROM reference_items WHERE school_id IS NULL"
        ))
    }
    for category, entries in GLOBAL_SEEDS.items():
        for order, (code, name) in enumerate(entries):
            if (category, code) in existing:
                continue
            bind.execute(
                sa.text(
                    "INSERT INTO reference_items (category, code, name, sort_order, is_active) "
                    "VALUES (:category, :code, :name, :sort_order, 1)"
                ),
                {"category": category, "code": code, "name": name, "sort_order": order},
            )


def downgrade() -> None:
    if _has_table("reference_items"):
        op.drop_table("reference_items")
