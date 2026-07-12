import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import agent_platform as R
from backend.services import agent_platform as svc


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
    tag = uuid.uuid4().hex[:5]
    u = models.User(email=f"u_{tag}@x.com", hashed_password="x", full_name=f"U {tag}", role=role,
                    school_id=school.id, is_active=True)
    db.add(u); db.commit()
    return u


def _ctx(db, user):
    return svc.AgentContext(user_id=user.id, school_id=user.school_id,
                            role=user.role.value, full_name=user.full_name, language="fr", db=db)


def test_capabilities_filtered_by_role():
    db = _session()
    school = _school(db)
    teacher = _user(db, school, models.UserRole.TEACHER)
    cashier = _user(db, school, models.UserRole.CASHIER)
    t = R.capabilities(current_user=teacher, db=db)
    assert "Academic Agent" in t["agents"] and "Finance Agent" not in t["agents"]
    c = R.capabilities(current_user=cashier, db=db)
    assert "Finance Agent" in c["agents"] and "Academic Agent" not in c["agents"]
    assert c["providers_configured"] is False  # empty registry


def test_provider_fallback_order_and_key_requirement(monkeypatch):
    db = _session()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    db.add(models.AIProvider(name="backup", provider_type="openrouter", priority=50,
                             is_active=True, api_key_encrypted=None))
    db.add(models.AIProvider(name="primary", provider_type="openai", priority=10,
                             is_active=True, api_key_encrypted=None))
    db.add(models.AIProvider(name="disabled", provider_type="deepseek", priority=1,
                             is_active=False, api_key_encrypted=None))
    db.commit()
    names = [p.name for p in svc.provider_candidates(db)]
    assert names == ["primary", "backup"]  # priority asc, inactive excluded
    # No decryptable key + no env key -> no model (never a fake client).
    assert all(svc.build_model_for(p) is None for p in svc.provider_candidates(db))
    model, provider = svc.resolve_model(db)
    assert model is None and provider is None


def test_agent_graph_respects_role_permissions():
    db = _session()
    school = _school(db)

    fake_model = "gpt-4.1-mini"  # plain string: graph building never needs a live provider

    student = _user(db, school, models.UserRole.STUDENT)
    coord = svc.build_agents(_ctx(db, student), fake_model)
    handoff_names = {getattr(h, "agent_name", getattr(h, "name", "")) for h in coord.handoffs}
    assert any("Academic" in n for n in handoff_names)
    assert not any("Finance" in n for n in handoff_names)

    accountant = _user(db, school, models.UserRole.ACCOUNTANT)
    coord2 = svc.build_agents(_ctx(db, accountant), fake_model)
    names2 = {getattr(h, "agent_name", getattr(h, "name", "")) for h in coord2.handoffs}
    assert any("Finance" in n for n in names2)
    assert not any("Tutor" in n for n in names2)


def test_stream_errors_cleanly_without_any_provider(monkeypatch):
    import asyncio

    db = _session()
    school = _school(db)
    teacher = _user(db, school, models.UserRole.TEACHER)
    from backend.services import ai_credits
    w = ai_credits.wallet_for_user(db, teacher); w.balance_credits = 100; db.commit()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    async def collect():
        return [e async for e in svc.stream_conversation(_ctx(db, teacher), "Bonjour")]

    events = asyncio.get_event_loop().run_until_complete(collect())
    assert events[-1]["type"] == "error"
    assert "provider" in events[-1]["message"].lower()  # clear message, no fake answer


def test_increment3_specialists_and_consult_tools():
    db = _session()
    school = _school(db)
    fake_model = "gpt-4.1-mini"

    # Admin gets every specialist, both as handoffs and as consult tools.
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)
    coord = svc.build_agents(_ctx(db, admin), fake_model)
    handoffs = {getattr(h, "agent_name", getattr(h, "name", "")) for h in coord.handoffs}
    assert {"Academic Agent", "Finance Agent", "Library Agent", "HR Agent", "Transport Agent"} <= handoffs
    tool_names = {getattr(t, "name", "") for t in coord.tools}
    assert {"consult_academic_agent", "consult_finance_agent", "consult_library_agent",
            "consult_hr_agent", "consult_transport_agent"} <= tool_names

    # A student can consult transport/library but never finance or HR.
    student = _user(db, school, models.UserRole.STUDENT)
    coord2 = svc.build_agents(_ctx(db, student), fake_model)
    tools2 = {getattr(t, "name", "") for t in coord2.tools}
    assert "consult_transport_agent" in tools2 and "consult_library_agent" in tools2
    assert "consult_finance_agent" not in tools2 and "consult_hr_agent" not in tools2

    # Capabilities endpoint mirrors the same gating.
    caps = R.capabilities(current_user=student, db=db)
    assert "Transport Agent" in caps["agents"] and "HR Agent" not in caps["agents"]
