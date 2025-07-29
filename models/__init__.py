from .base import Base, BaseModel
from .user import User, UserRole, UserBase, UserCreate, UserUpdate, UserInDB
from .conversation import Conversation, ConversationBase, ConversationCreate, ConversationUpdate, ConversationInDB
from .message import Message, MessageType, MessageBase, MessageCreate, MessageUpdate, MessageInDB

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    'Base', 'BaseModel',
    'User', 'UserRole', 'UserBase', 'UserCreate', 'UserUpdate', 'UserInDB',
    'Conversation', 'ConversationBase', 'ConversationCreate', 'ConversationUpdate', 'ConversationInDB',
    'Message', 'MessageType', 'MessageBase', 'MessageCreate', 'MessageUpdate', 'MessageInDB'
]
