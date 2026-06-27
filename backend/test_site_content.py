import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import site


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _users(db):
    super_admin = models.User(
        email="super-site@test.local",
        hashed_password="test",
        full_name="Super Site",
        role=models.UserRole.SUPER_ADMIN,
        is_active=True,
    )
    teacher = models.User(
        email="teacher-site@test.local",
        hashed_password="test",
        full_name="Teacher Site",
        role=models.UserRole.TEACHER,
        is_active=True,
    )
    db.add_all([super_admin, teacher])
    db.commit()
    return super_admin, teacher


def test_public_content_returns_defaults_when_empty():
    db = _session()
    content = site.get_site_content(db=db)
    assert content["hero"]["title"].startswith("TeducAI")
    assert set(["hero", "faq", "testimonials", "partners", "seo", "footer", "pricing"]).issubset(content.keys())


def test_super_admin_can_update_and_changes_are_public():
    db = _session()
    super_admin, _teacher = _users(db)
    updated = site.update_site_content(
        payload={"hero": {"title": "Nouveau titre"}, "faq": [{"question": "Q?", "answer": "A."}]},
        current_user=super_admin,
        db=db,
    )
    assert updated["hero"]["title"] == "Nouveau titre"
    # Untouched hero fields keep their defaults (deep merge).
    assert updated["hero"]["primary_cta_label"] == "Essayer Gratuitement"

    public = site.get_site_content(db=db)
    assert public["hero"]["title"] == "Nouveau titre"
    assert public["faq"] == [{"question": "Q?", "answer": "A."}]


def test_non_super_admin_cannot_update():
    db = _session()
    _super_admin, teacher = _users(db)
    with pytest.raises(HTTPException) as exc:
        site.update_site_content(payload={"hero": {"title": "x"}}, current_user=teacher, db=db)
    assert exc.value.status_code == 403


def test_unknown_sections_are_ignored():
    db = _session()
    super_admin, _teacher = _users(db)
    updated = site.update_site_content(
        payload={"malicious": {"x": 1}, "footer": {"tagline": "Pied"}},
        current_user=super_admin,
        db=db,
    )
    assert "malicious" not in updated
    assert updated["footer"]["tagline"] == "Pied"
