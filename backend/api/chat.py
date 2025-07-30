from fastapi import APIRouter, WebSocket, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4

from ..services.ai_chat import ai_chat_service
from ..websocket.chat import handle_websocket
from ..core.auth import get_current_user
from ..schemas.chat import ChatMessage, ChatSession, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.websocket("/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await handle_websocket(websocket, session_id)

@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create new chat session"""
    session_id = str(uuid4())
    session = await ai_chat_service.create_session(session_id)
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "messages": []
    }

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get existing chat session"""
    session = await ai_chat_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "messages": [msg.dict() for msg in session.messages]
    }

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    message: ChatMessage,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send message and get AI response"""
    response = await ai_chat_service.get_chat_response(
        session_id,
        message.content
    )
    
    return {
        "session_id": session_id,
        "response": response,
        "timestamp": datetime.now()
    }

@router.delete("/sessions/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clear chat session"""
    await ai_chat_service.clear_session(session_id)
    
    return {
        "status": "success",
        "message": "Chat session cleared",
        "session_id": session_id
    }

@router.post("/context")
async def add_context(
    texts: List[str],
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Add context documents for AI responses"""
    await ai_chat_service.add_context(texts)
    
    return {
        "status": "success",
        "message": f"Added {len(texts)} documents to context",
        "timestamp": datetime.now()
    }
