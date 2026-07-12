"""Multi-agent platform API — `/agents` (SSE streaming chat + capability list).

Thin transport over services/agent_platform.py: resolves the authenticated
caller into an AgentContext (tenant + role, never client-supplied) and relays
the normalized event stream as Server-Sent Events.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import database, models, security
from ..services import agent_platform

router = APIRouter(prefix="/agents", tags=["AI Agents"])


class AgentChatRequest(BaseModel):
    message: str
    history: Optional[list] = None  # result.to_input_list() from the previous turn
    language: Optional[str] = None


def _context(user: models.User, db: Session, language: Optional[str]) -> agent_platform.AgentContext:
    return agent_platform.AgentContext(
        user_id=user.id, school_id=user.school_id,
        role=getattr(user.role, "value", str(user.role)).lower(),
        full_name=user.full_name or user.email, language=language or "fr", db=db,
    )


@router.get("/capabilities")
def capabilities(current_user: models.User = Depends(security.get_current_user),
                 db: Session = Depends(database.get_db)):
    role = getattr(current_user.role, "value", str(current_user.role)).lower()
    agents = ["TeducAI Coordinator"]
    if role in agent_platform.ACADEMIC_ROLES:
        agents += ["Academic Agent", "Student Tutor Agent"]
    if role in agent_platform.FINANCE_ROLES:
        agents.append("Finance Agent")
    providers = [p.name for p in agent_platform.provider_candidates(db)]
    return {"agents": agents, "providers_configured": len(providers) > 0}


@router.post("/chat")
async def agent_chat(payload: AgentChatRequest,
                     current_user: models.User = Depends(security.get_current_user),
                     db: Session = Depends(database.get_db)):
    ctx = _context(current_user, db, payload.language)

    async def event_source():
        async for event in agent_platform.stream_conversation(ctx, payload.message, payload.history):
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
