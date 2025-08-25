from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.session import get_db
from ...models import User, Message, Conversation
from ...schemas.message import MessageCreate, MessageInDB, MessageUpdate
from ...core.security import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[MessageInDB])
def read_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve messages in a conversation
    """
    # Verify user has access to this conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    return messages

@router.post("/", response_model=MessageInDB)
def create_message(
    *,
    db: Session = Depends(get_db),
    message_in: MessageCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new message in a conversation
    """
    # Verify user has access to this conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == message_in.conversation_id,
        Conversation.owner_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    message = Message(
        **message_in.dict(exclude={"metadata"}),
        sender_id=current_user.id,
        metadata_=message_in.metadata or {},
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Update conversation's updated_at timestamp
    db.refresh(conversation)

    return message

@router.get("/{message_id}", response_model=MessageInDB)
def read_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get message by ID
    """
    message = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Message.id == message_id,
            Conversation.owner_id == current_user.id
        )
        .first()
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    return message

@router.put("/{message_id}", response_model=MessageInDB)
def update_message(
    *,
    db: Session = Depends(get_db),
    message_id: int,
    message_in: MessageUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a message
    """
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.sender_id == current_user.id  # Only sender can update
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied",
        )

    update_data = message_in.dict(exclude_unset=True)
    if "metadata" in update_data:
        update_data["metadata_"] = update_data.pop("metadata")

    for field, value in update_data.items():
        setattr(message, field, value)

    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.delete("/{message_id}")
def delete_message(
    *,
    db: Session = Depends(get_db),
    message_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a message
    """
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.sender_id == current_user.id  # Only sender can delete
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied",
        )

    db.delete(message)
    db.commit()
    return {"ok": True}
