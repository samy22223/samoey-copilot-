from sqlalchemy import Column, Text, Integer, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from .base import BaseModel, Base

class Message(BaseModel, Base):
    __tablename__ = "messages"

    content = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "is_user": self.is_user,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
