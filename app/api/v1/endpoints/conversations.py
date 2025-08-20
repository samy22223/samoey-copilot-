from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.db.session import get_db
from backend.models.conversation import Conversation
from backend.models.message import Message
from backend.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationInResponse,
    ConversationsInResponse
)
from backend.core.security import get_current_active_user
from backend.models.user import User

router = APIRouter()

@router.get("/", response_model=ConversationsInResponse)
async def read_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    count = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).count()
    
    return {"conversations": conversations, "count": count}

@router.post("/", response_model=ConversationInResponse)
async def create_conversation(
    conversation_in: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation = Conversation(
        **conversation_in.dict(),
        user_id=current_user.id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return {"conversation": conversation}

@router.get("/{conversation_id}", response_model=ConversationInResponse)
async def read_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {"conversation": conversation}

@router.put("/{conversation_id}", response_model=ConversationInResponse)
async def update_conversation(
    conversation_id: int,
    conversation_in: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    update_data = conversation_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)
    
    db.commit()
    db.refresh(conversation)
    
    return {"conversation": conversation}

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}
