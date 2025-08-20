from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """Chat message schema"""
    content: str
    role: Optional[str] = "user"
    timestamp: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Hello, how can you help me with coding?",
                "role": "user"
            }
        }

class ChatResponse(BaseModel):
    """Chat response schema"""
    session_id: str
    response: str
    timestamp: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "response": "I can help you with various coding tasks...",
                "timestamp": "2025-07-29T10:00:00Z"
            }
        }

class Message(BaseModel):
    """Message in chat session"""
    role: str
    content: str
    timestamp: datetime

class ChatSession(BaseModel):
    """Chat session schema"""
    session_id: str
    created_at: datetime
    messages: List[Message]
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-07-29T10:00:00Z",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, how can you help me?",
                        "timestamp": "2025-07-29T10:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "I can help you with various tasks...",
                        "timestamp": "2025-07-29T10:00:01Z"
                    }
                ]
            }
        }
