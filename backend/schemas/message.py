from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)
    is_user: bool = True

class MessageCreate(MessageBase):
    conversation_id: int

class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    is_user: Optional[bool] = None

class MessageInDBBase(MessageBase):
    id: int
    conversation_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class MessageInResponse(BaseModel):
    message: MessageInDBBase

class MessagesInResponse(BaseModel):
    messages: List[MessageInDBBase]
    count: int
