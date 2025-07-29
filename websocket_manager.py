import json
import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid
import logging

from ai_chat import get_chat_manager, AIChatManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_manager = get_chat_manager()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client connected: {client_id}")
        
        # Send welcome message
        welcome_msg = {
            "type": "system",
            "message": "Connected to Pinnacle Copilot. How can I assist you today?",
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_personal_message(json.dumps(welcome_msg), websocket)
    
    def disconnect(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client disconnected: {client_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: str):
        """Send a message to all connected clients"""
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
    
    async def handle_message(self, message: str, client_id: str):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "chat")
            
            if message_type == "chat":
                return await self._handle_chat_message(data, client_id)
            elif message_type == "command":
                return await self._handle_command(data, client_id)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {"error": "Unknown message type"}
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            return {"error": "Invalid JSON format"}
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {"error": str(e)}
    
    async def _handle_chat_message(self, data: Dict, client_id: str) -> Dict:
        """Handle chat messages"""
        message = data.get("message", "")
        language = data.get("language")
        
        if language:
            success, msg = self.chat_manager.set_language(language)
            if not success:
                return {"type": "error", "message": msg}
        
        # Process the message with the chat manager
        response = self.chat_manager.process_message(message, client_id)
        
        # Get recent chat history
        history = self.chat_manager.get_chat_history(limit=5)
        
        return {
            "type": "chat_response",
            "message": response,
            "history": history,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_command(self, data: Dict, client_id: str) -> Dict:
        """Handle special commands"""
        command = data.get("command", "")
        args = data.get("args", {})
        
        if command == "clear_history":
            self.chat_manager.clear_memory()
            return {"type": "system", "message": "Chat history cleared"}
            
        elif command == "set_language":
            language = args.get("language")
            if language:
                success, msg = self.chat_manager.set_language(language)
                return {"type": "system", "message": msg}
            
            return {"type": "error", "message": "No language specified"}
            
        elif command == "get_history":
            limit = args.get("limit", 10)
            history = self.chat_manager.get_chat_history(limit=limit)
            return {"type": "chat_history", "history": history}
            
        else:
            return {"type": "error", "message": f"Unknown command: {command}"}

# Global connection manager
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                
                # Process the message
                response = await manager.handle_message(data, client_id)
                
                # Send response back to client
                if response:
                    await manager.send_personal_message(json.dumps(response), websocket)
                    
            except WebSocketDisconnect:
                manager.disconnect(client_id)
                break
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                error_msg = {
                    "type": "error",
                    "message": f"An error occurred: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(json.dumps(error_msg), websocket)
                
    except Exception as e:
        logger.error(f"Connection error: {e}")
        
    finally:
        manager.disconnect(client_id)
