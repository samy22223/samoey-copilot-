from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from .base import BaseModel, Base

class Conversation(BaseModel, Base):
    __tablename__ = "conversations"

    title = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_archived = Column(Boolean, default=False)

    # Relationships
    owner = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def to_dict(self, include_messages=False):
        data = {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_messages:
            data["messages"] = [message.to_dict() for message in self.messages]

        return data
