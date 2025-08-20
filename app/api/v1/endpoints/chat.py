from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.config import settings
from app.db.session import get_db
from app.services.ai_chat import AIChatService

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    timestamp: str


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.post("/send")
async def send_message(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Send a message to the AI chat service.
    """
    try:
        ai_service = AIChatService()

        response = await ai_service.process_message(
            message=chat_message.message,
            conversation_id=chat_message.conversation_id,
            language=chat_message.language
        )

        return ChatResponse(
            response=response["response"],
            conversation_id=response["conversation_id"],
            message_id=response["message_id"],
            timestamp=response["timestamp"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get list of conversations for the current user.
    """
    try:
        ai_service = AIChatService()
        conversations = await ai_service.get_conversations(limit=limit, offset=offset)
        return {"conversations": conversations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation by ID.
    """
    try:
        ai_service = AIChatService()
        conversation = await ai_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a specific conversation.
    """
    try:
        ai_service = AIChatService()
        success = await ai_service.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time chat communication.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            # Process the message through AI service
            try:
                ai_service = AIChatService()
                response = await ai_service.process_message(
                    message=data,
                    conversation_id=client_id,
                    language="en"
                )

                # Send response back to the client
                await manager.send_personal_message(
                    f"AI Response: {response['response']}",
                    websocket
                )

            except Exception as e:
                await manager.send_personal_message(
                    f"Error: {str(e)}",
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left the chat")


@router.get("/models")
async def get_available_models():
    """
    Get list of available AI models.
    """
    try:
        ai_service = AIChatService()
        models = await ai_service.get_available_models()
        return {"models": models}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_conversation_history(
    conversation_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Clear conversation history for a specific conversation or all conversations.
    """
    try:
        ai_service = AIChatService()

        if conversation_id:
            success = await ai_service.clear_conversation(conversation_id)
            if not success:
                raise HTTPException(status_code=404, detail="Conversation not found")
            message = "Conversation cleared successfully"
        else:
            await ai_service.clear_all_conversations()
            message = "All conversations cleared successfully"

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
