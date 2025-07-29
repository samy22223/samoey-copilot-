from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .message import Message as MessageSchema

class ConversationBase(BaseModel):
    title: str = Field(..., max_length=200)
    is_archived: bool = False

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    is_archived: Optional[bool] = None

class ConversationInDBBase(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ConversationWithMessages(ConversationInDBBase):
    messages: List[MessageSchema] = []

class ConversationInResponse(BaseModel):
    conversation: ConversationInDBBase

class ConversationsInResponse(BaseModel):
    conversations: List[ConversationInDBBase]
    count: int
