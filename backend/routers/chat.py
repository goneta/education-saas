from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from backend.services.ai_service import ai_service

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    type: str # 'chat' or 'content'
    message: str
    data: Optional[Any] = None

@router.post("/", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    print(f"DEBUG: Received chat request: {request.message}")
    try:
        response = ai_service.generate_response(request.message)
        print(f"DEBUG: Generated response: {response}")
        return response
    except Exception as e:
        print(f"DEBUG: Error in chat_with_ai: {e}")
        raise HTTPException(status_code=500, detail=str(e))
