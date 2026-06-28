import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import ai_agents


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _user(db, role):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"Ag {uid}", domain_prefix=f"ag_{uid}", school_type=models.SchoolType.GENERAL)
    user = models.User(email=f"{role.value}_{uid}@ag.local", hashed_password="x", full_name="U", role=role, school=school, is_active=True)
    db.add_all([school, user])
    db.commit()
    return user


def test_registry_has_41_unique_agents_with_prompts():
    assert len(ai_agents.AGENTS) == 41
    assert len(ai_agents.AGENTS_BY_KEY) == 41
    for agent in ai_agents.AGENTS:
        # Every agent carries the shared security contract in its prompt.
        prompt = agent.system_prompt()
        assert "multi-tenant isolation" in prompt
        assert agent.permission and agent.keywords


def test_select_agent_routes_by_keyword():
    db = _session()
    admin = _user(db, models.UserRole.SUPER_ADMIN)
    assert ai_agents.select_agent("Quels sont les frais impayés ?", admin, db)["agent"].key == "finance_officer"
    assert ai_agents.select_agent("Optimise l'emploi du temps", admin, db)["agent"].key == "timetable_optimizer"
    assert ai_agents.select_agent("Montre les absences de la classe", admin, db)["agent"].key == "attendance_manager"


def test_unmatched_request_falls_back_to_coordinator():
    db = _session()
    admin = _user(db, models.UserRole.SUPER_ADMIN)
    routing = ai_agents.select_agent("zzzz qwerty random", admin, db)
    assert routing["agent"].key == "coordinator"
    assert routing["handoff"] is None


def test_routing_is_permission_aware():
    db = _session()
    # A student lacks finance:read -> finance agent selected but not authorized.
    student = _user(db, models.UserRole.STUDENT)
    routing = ai_agents.select_agent("Voir les paiements et factures", student, db)
    assert routing["agent"].key == "finance_officer"
    assert routing["authorized"] is False
    assert routing["refusal"]
    # Super admin is authorized everywhere.
    admin = _user(db, models.UserRole.SUPER_ADMIN)
    assert ai_agents.select_agent("Voir les paiements", admin, db)["authorized"] is True


def test_accessible_agents_filters_by_permission():
    db = _session()
    admin = _user(db, models.UserRole.SUPER_ADMIN)
    student = _user(db, models.UserRole.STUDENT)
    assert len(ai_agents.accessible_agents(admin, db)) == 41  # wildcard
    assert len(ai_agents.accessible_agents(student, db)) < 41


def test_llm_router_overrides_keyword_when_provider_available():
    db = _session()
    admin = _user(db, models.UserRole.SUPER_ADMIN)
    # The message has no library keywords, but the injected LLM router picks it.
    routing = ai_agents.select_agent(
        "Recommande quelque chose à lire pour un élève curieux",
        admin, db,
        classifier=lambda message, options: "library_manager",
    )
    assert routing["agent"].key == "library_manager"
    assert routing["method"] == "llm"
    assert routing["handoff"]


def test_llm_router_invalid_key_falls_back_to_keyword():
    db = _session()
    admin = _user(db, models.UserRole.SUPER_ADMIN)
    routing = ai_agents.select_agent(
        "Quels sont les frais impayés ?",
        admin, db,
        classifier=lambda message, options: "not_a_real_agent",
    )
    assert routing["agent"].key == "finance_officer"
    assert routing["method"] == "keyword"


def test_llm_router_failure_does_not_break_routing():
    db = _session()
    admin = _user(db, models.UserRole.SUPER_ADMIN)

    def boom(message, options):
        raise RuntimeError("provider down")

    routing = ai_agents.select_agent("Optimise l'emploi du temps", admin, db, classifier=boom)
    assert routing["agent"].key == "timetable_optimizer"
    assert routing["method"] == "keyword"
