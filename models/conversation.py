from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional

from .base import Base, BaseModel
from .user import User

class Conversation(Base, BaseModel):
    __tablename__ = "conversations"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    conversation_metadata = Column("metadata", JSON, default=dict, nullable=True)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation {self.id} - {self.title}>"
    
    @property
    def message_count(self) -> int:
        return len(self.messages)
    
    @property
    def last_message(self):
        return max(self.messages, key=lambda m: m.created_at) if self.messages else None

# Pydantic models for request/response validation
class ConversationBase(BaseModel):
    title: str
    is_archived: bool = False
    metadata: Optional[dict] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(ConversationBase):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    metadata: Optional[dict] = None

class ConversationInDB(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        orm_mode = True
