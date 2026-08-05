"""Hierarchical reference data: global TeducAI lists + per-school extensions.

Rules under test (see services/reference_data.py):
- global items are visible to every school, read-only for schools;
- a school's local items are visible ONLY to that school, merged into one list;
- school admins create/update/delete ONLY their local items (403 on global);
- the Super Admin manages the global lists (and may inspect/act anywhere);
- the school_level category merges the EXISTING SchoolLevel referential.
Self-contained in-memory DB.
"""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import reference_data


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _user(db, school, role):
    tag = uuid.uuid4().hex[:6]
    u = models.User(email=f"u_{tag}@x.com", hashed_password="x", full_name="U", role=role,
                    school_id=school.id if school else None, is_active=True)
    db.add(u); db.commit()
    return u


def test_merge_global_and_local_and_isolation():
    db = _session()
    school_a, school_b = _school(db), _school(db)
    superadmin = _user(db, None, models.UserRole.SUPER_ADMIN)
    admin_a = _user(db, school_a, models.UserRole.SCHOOL_ADMIN)

    # Super Admin creates a GLOBAL fee type; school A adds a LOCAL one.
    reference_data.create_item(db, "fee_type", current_user=superadmin, name="Scolarité", code="TUITION")
    reference_data.create_item(db, "fee_type", current_user=admin_a, name="Frais de laboratoire")
    db.commit()

    merged_a = reference_data.merged_items(db, "fee_type", school_a.id)
    codes_a = {(item["code"], item["scope"]) for item in merged_a}
    assert ("TUITION", "global") in codes_a
    assert ("FRAIS_DE_LABORATOIRE", "school") in codes_a

    # School B sees the global item but NOT school A's local addition.
    merged_b = reference_data.merged_items(db, "fee_type", school_b.id)
    codes_b = {(item["code"], item["scope"]) for item in merged_b}
    assert ("TUITION", "global") in codes_b
    assert all(code != "FRAIS_DE_LABORATOIRE" for code, _ in codes_b)


def test_school_cannot_touch_global_items():
    db = _session()
    school = _school(db)
    superadmin = _user(db, None, models.UserRole.SUPER_ADMIN)
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)

    item = reference_data.create_item(db, "leave_type", current_user=superadmin, name="Congé annuel")
    db.commit()

    # Neither create-global, nor update, nor delete.
    with pytest.raises(HTTPException) as exc:
        reference_data.create_item(db, "leave_type", current_user=admin, name="X", scope="global")
    assert exc.value.status_code == 403
    with pytest.raises(HTTPException) as exc:
        reference_data.update_item(db, item["id"], current_user=admin, data={"name": "Hack"})
    assert exc.value.status_code == 403
    with pytest.raises(HTTPException) as exc:
        reference_data.delete_item(db, item["id"], current_user=admin)
    assert exc.value.status_code == 403

    # The Super Admin can.
    updated = reference_data.update_item(db, item["id"], current_user=superadmin, data={"name": "Congé annuel payé"})
    assert updated["name"] == "Congé annuel payé"
    reference_data.delete_item(db, item["id"], current_user=superadmin)
    db.commit()
    assert reference_data.merged_items(db, "leave_type", school.id) == []


def test_local_item_lifecycle_and_cross_school_guard():
    db = _session()
    school_a, school_b = _school(db), _school(db)
    admin_a = _user(db, school_a, models.UserRole.SCHOOL_ADMIN)
    admin_b = _user(db, school_b, models.UserRole.SCHOOL_ADMIN)

    item = reference_data.create_item(db, "room_type", current_user=admin_a, name="Salle de musique")
    db.commit()
    assert item["scope"] == "school" and item["school_id"] == school_a.id

    # The owning school manages it; another school gets 403.
    with pytest.raises(HTTPException) as exc:
        reference_data.update_item(db, item["id"], current_user=admin_b, data={"name": "X"})
    assert exc.value.status_code == 403
    reference_data.update_item(db, item["id"], current_user=admin_a, data={"name": "Salle de musique 2"})
    reference_data.delete_item(db, item["id"], current_user=admin_a)
    db.commit()
    assert reference_data.merged_items(db, "room_type", school_a.id) == []

    # Duplicate code in the same merged view -> 409.
    reference_data.create_item(db, "room_type", current_user=admin_a, name="Dojo", code="DOJO")
    with pytest.raises(HTTPException) as exc:
        reference_data.create_item(db, "room_type", current_user=admin_a, name="Dojo bis", code="DOJO")
    assert exc.value.status_code == 409


def test_school_level_category_merges_existing_referential():
    db = _session()
    school = _school(db)
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)
    db.add(models.SchoolLevel(code="CP1", name="Cours préparatoire 1", sort_order=1, is_active=True))
    db.commit()

    reference_data.create_item(db, "school_level", current_user=admin, name="Prépa BTS", code="PREPA_BTS")
    db.commit()
    merged = reference_data.merged_items(db, "school_level", school.id)
    by_code = {item["code"]: item for item in merged}
    assert by_code["CP1"]["scope"] == "global" and by_code["CP1"]["source"] == "levels"
    assert by_code["PREPA_BTS"]["scope"] == "school" and by_code["PREPA_BTS"]["source"] == "reference"


def test_unknown_category_404():
    db = _session()
    with pytest.raises(HTTPException) as exc:
        reference_data.merged_items(db, "not_a_category", None)
    assert exc.value.status_code == 404
