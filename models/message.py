from sqlalchemy import Column, Text, Boolean, Integer, ForeignKey, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import enum

from .base import Base, BaseModel
from .conversation import Conversation

class MessageType(str, enum.Enum):
    TEXT = "text"
    CODE = "code"
    ERROR = "error"
    SYSTEM = "system"
    COMMAND = "command"
    RESULT = "result"

class Message(Base, BaseModel):
    __tablename__ = "messages"
    
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    is_user = Column(Boolean, default=True, nullable=False)  # True for user, False for AI
    message_metadata = Column(JSON, default=dict, nullable=True)  # Additional metadata like tokens, model used, etc.
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} - {'User' if self.is_user else 'AI'}>"
    
    @property
    def is_ai(self) -> bool:
        return not self.is_user

# Pydantic models for request/response validation
class MessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT
    is_user: bool = True
    metadata: Optional[dict] = None

class MessageCreate(MessageBase):
    conversation_id: int

class MessageUpdate(MessageBase):
    content: Optional[str] = None
    message_type: Optional[MessageType] = None
    is_user: Optional[bool] = None
    metadata: Optional[dict] = None

class MessageInDB(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
