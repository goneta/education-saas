from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any
from backend import models, security
from backend.services.ai_service import ai_service

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    type: str # 'chat' or 'content'
    message: str
    data: Optional[Any] = None

@router.post("/", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, current_user: models.User = Depends(security.get_current_user)):
    try:
        response = ai_service.generate_response(request.message)
        return response
    except Exception:
        raise HTTPException(status_code=500, detail="AI service failed")
