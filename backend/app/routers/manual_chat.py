from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..models import User
from ..rag_chat_store import get_engine, reset_engine
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/manual", tags=["manual-chat"])


@router.post("/chat", response_model=ChatResponse, status_code=201)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    engine = get_engine(current_user.id)
    result = engine.chat(payload.message)
    return result


@router.post("/reset", status_code=204)
def reset_chat(current_user: User = Depends(get_current_user)):
    reset_engine(current_user.id)
