from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import User, Conversation
from ....schemas.conversation import ConversationCreate, ConversationInDB, ConversationUpdate
from ....core.security import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[ConversationInDB])
def read_conversations(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve conversations for the current user
    """
    conversations = db.query(Conversation).filter(
        Conversation.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    return conversations

@router.post("/", response_model=ConversationInDB)
def create_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_in: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new conversation
    """
    conversation = Conversation(
        **conversation_in.dict(),
        owner_id=current_user.id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@router.get("/{conversation_id}", response_model=ConversationInDB)
def read_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get conversation by ID
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation

@router.put("/{conversation_id}", response_model=ConversationInDB)
def update_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    conversation_in: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a conversation
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    update_data = conversation_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@router.delete("/{conversation_id}")
def delete_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a conversation
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    db.delete(conversation)
    db.commit()
    return {"ok": True}
