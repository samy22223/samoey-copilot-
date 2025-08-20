#!/usr/bin/env python3
"""
Initialize the database with sample data.
"""
import asyncio
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from db.session import engine
from models.user import User, UserCreate
from models.conversation import Conversation, Message, MessageRole
from core.security import get_password_hash
from crud import crud_user, crud_conversation, crud_message

# Sample data
SAMPLE_USERS = [
    {
        "email": "admin@pinnacle.local",
        "password": "admin123",
        "full_name": "Admin User",
        "is_superuser": True,
    },
    {
        "email": "user@pinnacle.local",
        "password": "user123",
        "full_name": "Regular User",
        "is_superuser": False,
    },
]

SAMPLE_CONVERSATIONS = [
    {
        "title": "Welcome to Pinnacle Copilot",
        "description": "Getting started with the AI assistant",
        "user_email": "user@pinnacle.local",
        "messages": [
            {
                "role": MessageRole.ASSISTANT,
                "content": "Hello! I'm Pinnacle Copilot, your AI development assistant. How can I help you today?",
            },
            {
                "role": MessageRole.USER,
                "content": "Can you help me set up a new Python project?",
            },
            {
                "role": MessageRole.ASSISTANT,
                "content": "Of course! I can help you set up a new Python project. What kind of project are you thinking of?",
            },
        ],
    },
]


async def init_db(session: AsyncSession) -> None:
    """Initialize the database with sample data."""
    # Create users
    users: Dict[str, User] = {}
    for user_data in SAMPLE_USERS:
        email = user_data["email"]
        existing_user = await crud_user.get_by_email(session, email=email)
        if not existing_user:
            user_in = UserCreate(
                email=email,
                password=user_data["password"],
                full_name=user_data["full_name"],
                is_superuser=user_data["is_superuser"],
            )
            user = await crud_user.create(session, obj_in=user_in)
            users[email] = user
            print(f"Created user: {email}")
        else:
            users[email] = existing_user
            print(f"User already exists: {email}")

    # Create conversations and messages
    for conv_data in SAMPLE_CONVERSATIONS:
        user_email = conv_data["user_email"]
        user = users.get(user_email)
        if not user:
            print(f"User not found: {user_email}")
            continue

        # Create conversation
        conversation_in = {
            "title": conv_data["title"],
            "description": conv_data["description"],
            "user_id": user.id,
        }
        conversation = await crud_conversation.create(session, obj_in=conversation_in)
        print(f"Created conversation: {conversation.title}")

        # Add messages
        for msg_data in conv_data["messages"]:
            message_in = {
                "role": msg_data["role"],
                "content": msg_data["content"],
                "conversation_id": conversation.id,
                "user_id": user.id if msg_data["role"] == MessageRole.USER else None,
            }
            await crud_message.create(session, obj_in=message_in)
        print(f"Added {len(conv_data['messages'])} messages to conversation")


async def main() -> None:
    """Run database initialization."""
    print("Initializing database...")
    
    async with sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )() as session:
        try:
            await init_db(session)
            await session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            await session.rollback()
            print(f"Error initializing database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
