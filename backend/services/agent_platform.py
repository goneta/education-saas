"""TeducAI Multi-Agent Platform — OpenAI Agents SDK foundation (increment 1).

Built on the `openai-agents` SDK (Agent/Runner loop, handoffs, function tools,
streaming) and wired into TeducAI's EXISTING AI infrastructure — zero
duplication: providers come from the `AIProvider` registry (encrypted keys,
priority order, base_url per provider → multi-provider fallback), spending is
gated through `ai_credits` (ensure_credits/record_usage), and every tool is
tenant-scoped + RBAC-checked against the calling user.

Increment 1 scope: Coordinator + Academic + Finance + Student-Tutor agents,
four read-only data tools, provider fallback, SSE streaming events. Further
agents/tools plug into AGENT_BUILDERS/TOOLS without touching the runtime.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from sqlalchemy.orm import Session

from .. import crypto_utils, models
from . import ai_credits

logger = logging.getLogger("teducai.agent_platform")

# Roles allowed to reach each specialist. The coordinator only exposes the
# handoffs the caller's role is entitled to — RBAC happens at graph-build time
# AND inside every tool (defence in depth).
FINANCE_ROLES = {"super_admin", "school_admin", "director", "accountant", "cashier", "parent"}
ACADEMIC_ROLES = {"super_admin", "school_admin", "director", "teacher", "student", "parent"}


@dataclass
class AgentContext:
    """Per-request context every tool receives (never trusted from the client)."""

    user_id: int
    school_id: Optional[int]
    role: str
    full_name: str
    language: str
    db: Session  # request-scoped SQLAlchemy session

    def require_school(self) -> int:
        if not self.school_id:
            raise ValueError("School context is required for this tool.")
        return self.school_id


# --- Provider fallback (reuses the AIProvider registry) -----------------------

def provider_candidates(db: Session) -> list[models.AIProvider]:
    return (
        db.query(models.AIProvider)
        .filter(models.AIProvider.is_active.is_(True))
        .order_by(models.AIProvider.priority.asc(), models.AIProvider.id.asc())
        .all()
    )


def build_model_for(provider: models.AIProvider):
    """An Agents-SDK model bound to one registry provider (base_url + key)."""
    from agents import OpenAIChatCompletionsModel
    from openai import AsyncOpenAI

    api_key = crypto_utils.decrypt_secret(provider.api_key_encrypted) or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    client = AsyncOpenAI(api_key=api_key, base_url=provider.base_url or None)
    return OpenAIChatCompletionsModel(model=provider.default_model or "gpt-4.1-mini", openai_client=client)


def resolve_model(db: Session):
    """First configured provider wins; the caller retries down the list on
    failure (see stream_conversation) — that is the automatic fallback."""
    for provider in provider_candidates(db):
        model = build_model_for(provider)
        if model is not None:
            return model, provider
    # Env-key fallback so a bare OPENAI_API_KEY works with no registry rows.
    if os.getenv("OPENAI_API_KEY"):
        from agents import OpenAIChatCompletionsModel
        from openai import AsyncOpenAI

        return OpenAIChatCompletionsModel(
            model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4.1-mini"),
            openai_client=AsyncOpenAI(),
        ), None
    return None, None


# --- Tools (tenant-scoped, RBAC inside) ---------------------------------------

def _tools():
    from agents import RunContextWrapper, function_tool

    # `from __future__ import annotations` stringifies hints; function_tool
    # re-evaluates them against module globals, so the lazy import must be
    # visible there for the ctx parameter to resolve.
    globals()["RunContextWrapper"] = RunContextWrapper

    @function_tool
    def search_students(ctx: RunContextWrapper[AgentContext], name: str) -> str:
        """Search students of the caller's school by (partial) name. Returns
        id, name, matricule and current class."""
        c = ctx.context
        if c.role not in ACADEMIC_ROLES:
            return "Access denied: your role cannot look up students."
        school_id = c.require_school()
        rows = (
            c.db.query(models.StudentProfile, models.User)
            .join(models.User, models.User.id == models.StudentProfile.user_id)
            .filter(models.User.school_id == school_id,
                    models.User.full_name.ilike(f"%{name}%"))
            .limit(10).all()
        )
        if c.role == "student":
            rows = [(p, u) for p, u in rows if u.id == c.user_id]
        out = [{"student_id": p.id, "name": u.full_name, "matricule": p.registration_number,
                "class_id": p.current_class_id} for p, u in rows]
        return json.dumps(out, ensure_ascii=False) if out else "No matching student in this school."

    @function_tool
    def lookup_grades(ctx: RunContextWrapper[AgentContext], student_id: int) -> str:
        """Latest grades for a student of the caller's school (max 15)."""
        c = ctx.context
        if c.role not in ACADEMIC_ROLES:
            return "Access denied."
        school_id = c.require_school()
        q = (
            c.db.query(models.Grade, models.Assessment, models.Subject, models.User)
            .join(models.Assessment, models.Assessment.id == models.Grade.assessment_id)
            .join(models.Subject, models.Subject.id == models.Assessment.subject_id)
            .join(models.StudentProfile, models.StudentProfile.id == models.Grade.student_id)
            .join(models.User, models.User.id == models.StudentProfile.user_id)
            .filter(models.Grade.student_id == student_id, models.User.school_id == school_id)
        )
        if c.role == "student":
            q = q.filter(models.User.id == c.user_id)
        rows = q.order_by(models.Grade.id.desc()).limit(15).all()
        out = [{"subject": s.name, "assessment": a.title, "score": g.score,
                "max_score": a.max_score, "comment": g.comment} for g, a, s, _u in rows]
        return json.dumps(out, ensure_ascii=False) if out else "No grades found for this student."

    @function_tool
    def lookup_attendance(ctx: RunContextWrapper[AgentContext], student_id: int) -> str:
        """Recent attendance records for a student of the caller's school (max 20)."""
        c = ctx.context
        if c.role not in ACADEMIC_ROLES:
            return "Access denied."
        school_id = c.require_school()
        rows = (
            c.db.query(models.Attendance)
            .join(models.StudentProfile, models.StudentProfile.id == models.Attendance.student_id)
            .join(models.User, models.User.id == models.StudentProfile.user_id)
            .filter(models.Attendance.student_id == student_id, models.User.school_id == school_id)
            .order_by(models.Attendance.id.desc()).limit(20).all()
        )
        out = [{"date": str(r.date), "status": getattr(r.status, "value", str(r.status))} for r in rows]
        return json.dumps(out, ensure_ascii=False) if out else "No attendance records found."

    @function_tool
    def lookup_invoices(ctx: RunContextWrapper[AgentContext], student_id: int) -> str:
        """Unpaid/paid fee invoices for a student of the caller's school (max 15)."""
        c = ctx.context
        if c.role not in FINANCE_ROLES:
            return "Access denied: your role cannot view finances."
        school_id = c.require_school()
        rows = (
            c.db.query(models.StudentInvoice)
            .filter(models.StudentInvoice.school_id == school_id,
                    models.StudentInvoice.student_id == student_id)
            .order_by(models.StudentInvoice.id.desc()).limit(15).all()
        )
        out = [{"number": r.invoice_number, "title": r.title, "due": r.amount_due,
                "paid": r.amount_paid, "remaining": r.remaining_balance,
                "status": getattr(r.status, "value", str(r.status))} for r in rows]
        return json.dumps(out, ensure_ascii=False) if out else "No invoices found for this student."

    return search_students, lookup_grades, lookup_attendance, lookup_invoices


# --- Agent graph ---------------------------------------------------------------

def build_agents(ctx: AgentContext, model):
    """Coordinator + role-filtered specialists. Handoffs only include agents
    the caller's role may reach."""
    from agents import Agent

    search_students, lookup_grades, lookup_attendance, lookup_invoices = _tools()
    base = (
        f"You are part of TeducAI, a school management platform. Caller: {ctx.full_name} "
        f"(role: {ctx.role}, school #{ctx.school_id}). Reply in the caller's language "
        f"({ctx.language}). Use ONLY tool data for facts about the school — never invent "
        "students, grades or amounts. If a tool denies access, say so plainly."
    )

    academic = Agent[AgentContext](
        name="Academic Agent",
        handoff_description="Grades, assessments, attendance, academic progress questions.",
        instructions=base + " You are the academic specialist: look up grades and "
        "attendance, explain progress, suggest concrete next steps for improvement.",
        tools=[search_students, lookup_grades, lookup_attendance], model=model,
    )
    tutor = Agent[AgentContext](
        name="Student Tutor Agent",
        handoff_description="Explaining concepts, study plans, revision help for students.",
        instructions=base + " You are a patient tutor: explain concepts step by step, "
        "adapt to the student's level, and propose short practice exercises.",
        tools=[lookup_grades], model=model,
    )
    finance = Agent[AgentContext](
        name="Finance Agent",
        handoff_description="School fees, invoices, payment status questions.",
        instructions=base + " You are the finance specialist: look up invoices and "
        "balances, explain what is due and how to pay (CinetPay mobile money or cash "
        "at the school). Never promise waivers.",
        tools=[search_students, lookup_invoices], model=model,
    )

    specialists = []
    if ctx.role in ACADEMIC_ROLES:
        specialists += [academic, tutor]
    if ctx.role in FINANCE_ROLES:
        specialists.append(finance)

    coordinator = Agent[AgentContext](
        name="TeducAI Coordinator",
        instructions=base + " You are the coordinator: answer directly when trivial, "
        "otherwise hand off to the right specialist. For multi-part questions, hand "
        "off sequentially and combine what you learn into ONE final answer.",
        handoffs=specialists, tools=[search_students] if ctx.role in ACADEMIC_ROLES else [],
        model=model,
    )
    return coordinator


# --- Streaming runtime ----------------------------------------------------------

async def stream_conversation(ctx: AgentContext, message: str,
                              history: Optional[list] = None) -> AsyncIterator[dict]:
    """Run one coordinator turn, yielding normalized SSE-ready events:
    {type: start|delta|tool|handoff|done|error, ...}. Tries providers in
    registry priority order — automatic fallback on any provider failure."""
    from agents import Runner, set_tracing_disabled

    user = ctx.db.query(models.User).filter(models.User.id == ctx.user_id).first()
    prompt_estimate = message + json.dumps(history or [])[:2000]
    ai_credits.ensure_credits(ctx.db, user, ai_credits.estimate_credits(prompt_estimate))

    if not os.getenv("OPENAI_API_KEY"):
        set_tracing_disabled(True)  # tracing export needs an OpenAI key

    candidates = provider_candidates(ctx.db)
    attempts = [(build_model_for(p), p) for p in candidates]
    attempts = [(m, p) for m, p in attempts if m is not None]
    if not attempts:
        model, provider = resolve_model(ctx.db)
        if model is None:
            yield {"type": "error", "message": "No AI provider is configured. Ask your administrator to add one in AI Providers."}
            return
        attempts = [(model, provider)]

    run_input = (history or []) + [{"role": "user", "content": message}]
    last_error: Optional[Exception] = None
    for model, provider in attempts:
        coordinator = build_agents(ctx, model)
        try:
            result = Runner.run_streamed(coordinator, run_input, context=ctx, max_turns=8)
            yield {"type": "start", "agent": coordinator.name,
                   "provider": provider.name if provider else "env:openai"}
            final_text = ""
            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    delta = getattr(event.data, "delta", None)
                    if isinstance(delta, str) and delta:
                        final_text += delta
                        yield {"type": "delta", "text": delta}
                elif event.type == "agent_updated_stream_event":
                    yield {"type": "handoff", "agent": event.new_agent.name}
                elif event.type == "run_item_stream_event":
                    item = event.item
                    if item.type == "tool_call_item":
                        yield {"type": "tool", "status": "started",
                               "name": getattr(item.raw_item, "name", "tool")}
                    elif item.type == "tool_call_output_item":
                        yield {"type": "tool", "status": "finished"}
            ai_credits.record_usage(ctx.db, user, message, final_text, "agent_platform", "chat")
            ctx.db.commit()
            yield {"type": "done", "agent": result.last_agent.name if result.last_agent else None,
                   "history": result.to_input_list()}
            return
        except Exception as exc:  # provider failure → automatic fallback
            last_error = exc
            logger.warning("Agent run failed on provider %s: %s — falling back",
                           provider.name if provider else "env", exc)
            continue
    yield {"type": "error", "message": f"All AI providers failed: {last_error}"}
