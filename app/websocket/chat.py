from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from datetime import datetime

from ..services.ai_chat import ai_chat_service
from ..core.logging import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect websocket client"""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect websocket client"""
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def broadcast(self, message: str, session_id: str):
        """Broadcast message to all connected clients in session"""
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(message)
                except WebSocketDisconnect:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection, session_id)

# Create singleton instance
manager = ConnectionManager()

async def handle_websocket(websocket: WebSocket, session_id: str):
    """Handle WebSocket connection"""
    try:
        await manager.connect(websocket, session_id)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Log received message
                logger.info(f"Received message in session {session_id}: {message_data}")
                
                if message_data["type"] == "message":
                    # Get AI response
                    response = await ai_chat_service.get_chat_response(
                        session_id,
                        message_data["content"]
                    )
                    
                    # Broadcast response to all clients in session
                    await manager.broadcast(
                        json.dumps({
                            "type": "message",
                            "role": "assistant",
                            "content": response,
                            "timestamp": datetime.now().isoformat()
                        }),
                        session_id
                    )
                    
                elif message_data["type"] == "clear":
                    # Clear chat session
                    await ai_chat_service.clear_session(session_id)
                    
                    # Notify clients
                    await manager.broadcast(
                        json.dumps({
                            "type": "session_cleared",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }),
                        session_id
                    )
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid message format in session {session_id}")
                continue
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)
        logger.info(f"Client disconnected from session {session_id}")
    
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {str(e)}")
        await manager.disconnect(websocket, session_id)
