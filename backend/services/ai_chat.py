from typing import List, Optional, Dict, Any
import openai
import asyncio
from datetime import datetime
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel

from config.settings import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

class Message(BaseModel):
    """Chat message model"""
    role: str
    content: str
    timestamp: datetime = datetime.now()

class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str
    messages: List[Message] = []
    context: Dict[str, Any] = {}
    created_at: datetime = datetime.now()
    
    class Config:
        arbitrary_types_allowed = True

class AIChatService:
    """AI Chat Service"""
    
    def __init__(self):
        """Initialize AI Chat Service"""
        self.openai = openai
        self.openai.api_key = settings.OPENAI_API_KEY
        self.sessions: Dict[str, ChatSession] = {}
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize text splitter for context
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    async def create_session(self, session_id: str) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(session_id=session_id)
        self.sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get existing chat session"""
        return self.sessions.get(session_id)
    
    async def add_message(self, session_id: str, role: str, content: str) -> Message:
        """Add message to chat session"""
        session = await self.get_session(session_id)
        if not session:
            session = await self.create_session(session_id)
        
        message = Message(role=role, content=content)
        session.messages.append(message)
        return message
    
    async def get_chat_response(self, session_id: str, message: str) -> str:
        """Get AI response for user message"""
        try:
            # Get or create session
            session = await self.get_session(session_id)
            if not session:
                session = await self.create_session(session_id)
            
            # Add user message
            await self.add_message(session_id, "user", message)
            
            # Format conversation history
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in session.messages[-10:]  # Get last 10 messages for context
            ]
            
            # Get relevant context if available
            if self.vector_store:
                context_docs = self.vector_store.similarity_search(message, k=3)
                context = "\n".join(doc.page_content for doc in context_docs)
                messages.insert(0, {
                    "role": "system",
                    "content": f"Context:\n{context}\n\nRespond based on the above context."
                })
            
            # Get AI response
            response = await asyncio.to_thread(
                self.openai.ChatCompletion.create,
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=settings.MAX_TOKENS,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract and store response
            ai_message = response.choices[0].message.content
            await self.add_message(session_id, "assistant", ai_message)
            
            return ai_message
            
        except Exception as e:
            logger.error(f"Error getting chat response: {str(e)}")
            return "I apologize, but I encountered an error processing your request."
    
    async def add_context(self, texts: List[str]) -> None:
        """Add context documents to vector store"""
        try:
            # Split texts into chunks
            docs = []
            for text in texts:
                chunks = self.text_splitter.split_text(text)
                docs.extend(chunks)
            
            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_texts(
                    docs,
                    self.embeddings
                )
            else:
                self.vector_store.add_texts(docs)
                
            logger.info(f"Added {len(docs)} document chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding context: {str(e)}")
    
    async def clear_session(self, session_id: str) -> None:
        """Clear chat session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Create singleton instance
ai_chat_service = AIChatService()
