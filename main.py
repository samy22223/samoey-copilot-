from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
import uvicorn
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

# Import models, schemas, and database
from models import User, Conversation, Message, UserRole
from schemas import UserCreate, UserResponse, MessageCreate, MessageResponse, \
    ConversationCreate, ConversationResponse
from database import engine, get_db, init_db

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/pinnacle_copilot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Pinnacle Copilot API",
    description="REST API for Pinnacle Copilot - AI-powered development assistant",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# API Routes

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Root endpoint that serves the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """Chat interface endpoint."""
    return templates.TemplateResponse("chat.html", {"request": request})

# User endpoints
@app.post("/api/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        user_preferences={"theme": "dark", "notifications": True}
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Conversation endpoints
@app.post("/api/conversations/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(conversation: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation."""
    # Check if user exists
    db_user = db.query(User).filter(User.id == conversation.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create conversation
    db_conversation = Conversation(
        title=conversation.title,
        user_id=conversation.user_id,
        conversation_metadata={"model": "gpt-4"}  # Default model
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def read_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get a specific conversation by ID with its messages."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.get("/api/conversations/", response_model=List[ConversationResponse])
def list_conversations(user_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List conversations for a specific user with pagination."""
    conversations = db.query(Conversation)\
        .filter(Conversation.user_id == user_id)\
        .order_by(Conversation.updated_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return conversations

# Message endpoints
@app.post("/api/messages/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    """Create a new message in a conversation."""
    # Verify conversation exists
    db_conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create message
    db_message = Message(
        content=message.content,
        is_user=message.is_user,
        conversation_id=message.conversation_id,
        message_metadata={"tokens": len(message.content.split())}  # Simple token count
    )
    
    db.add(db_message)
    
    # Update conversation's updated_at
    db_conversation.updated_at = datetime.utcnow()
    
    # If this is the first message, update the conversation title
    if not db_conversation.title and message.is_user:
        # Use first few words of the message as title
        db_conversation.title = ' '.join(message.content.split()[:5]) + '...'
    
    db.commit()
    db.refresh(db_message)
    
    return db_message

@app.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(conversation_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get messages for a specific conversation with pagination."""
    # Verify conversation exists
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at.asc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return messages

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
