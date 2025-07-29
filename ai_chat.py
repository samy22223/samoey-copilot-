import os
import json
import importlib
from typing import Dict, List, Optional, Any, Type, Union
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path

# Optional AI/ML imports
try:
    import torch
    from langchain.llms import OpenAI, HuggingFacePipeline
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import PromptTemplate
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.document_loaders import TextLoader
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("AI/ML dependencies not found. Some features will be disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Language(str, Enum):
    ENGLISH = "en"
    FRENCH = "fr"

class AIChatManager:
    def __init__(self, use_local: bool = False, model_name: str = "gpt-3.5-turbo"):
        """Initialize the AI chat manager"""
        self.use_local = use_local
        self.model_name = model_name
        self.language = "en"  # Default to English
        self.custom_instructions = self._load_custom_instructions()
        self.llm = self._init_llm()
        self.knowledge_base = self._init_knowledge_base()
        
        # Initialize memory and conversation
        self.memory = self._init_memory()
        self.conversation = self._init_conversation()
        self.chat_history = []
        
        # Load initial system prompt
        self.system_prompt = self._get_system_prompt()

    def _init_llm(self):
        """Initialize the language model"""
        if not AI_AVAILABLE:
            return self._create_dummy_llm()
            
        try:
            if self.use_local:
                # Use local model if available
                try:
                    from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
                    
                    model_name = "gpt2"  # Default to a smaller model
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForCausalLM.from_pretrained(model_name)
                    pipe = pipeline(
                        "text-generation",
                        model=model,
                        tokenizer=tokenizer,
                        max_length=100,
                        temperature=0.7,
                        top_p=0.95,
                        repetition_penalty=1.15
                    )
                    return HuggingFacePipeline(pipeline=pipe)
                except Exception as e:
                    logger.warning(f"Failed to load local model: {e}. Falling back to simple mode.")
                    self.use_local = False
            
            # Try to use OpenAI if available
            try:
                from langchain.llms import OpenAI
                return OpenAI(temperature=0.7, model_name=self.model_name)
            except ImportError:
                logger.warning("OpenAI not available. Using simple mode.")
                return self._create_dummy_llm()
                
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            return self._create_dummy_llm()
            
    def _create_dummy_llm(self):
        """Create a simple LLM that works without AI dependencies"""
        class DummyLLM:
            def predict(self, input_text, **kwargs):
                return "I'm running in simple mode. Please install AI dependencies for full functionality.\n\n" \
                      "To enable AI features, install with: pip install torch transformers sentence-transformers langchain"
                      
            def __call__(self, input_text, **kwargs):
                return self.predict(input_text, **kwargs)
                
        return DummyLLM()
    
    def _init_knowledge_base(self):
        """Initialize the knowledge base with system documentation"""
        if not AI_AVAILABLE:
            return self._create_dummy_knowledge_base()
            
        try:
            from langchain.embeddings import HuggingFaceEmbeddings
            from langchain.vectorstores import Chroma
            from langchain.docstore.document import Document
            
            embeddings = HuggingFaceEmbeddings()
            persist_directory = "data/vectorstore"
            
            # Create directory if it doesn't exist
            os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize with empty documents if none exist
            if not os.path.exists(os.path.join(persist_directory, "chroma.sqlite3")):
                docs = [Document(page_content="Pinnacle Copilot is an AI assistant.")]
                return Chroma.from_documents(docs, embeddings, persist_directory=persist_directory)
            
            return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
            
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {e}")
            return self._create_dummy_knowledge_base()
            
    def _create_dummy_knowledge_base(self):
        """Create a simple knowledge base that works without AI dependencies"""
        class DummyKnowledgeBase:
            def similarity_search(self, query, k=1):
                return [{"page_content": "AI features are not available. Install dependencies to enable full functionality."}]
                
            def add_documents(self, documents):
                return True
                
            def persist(self):
                pass
                
        return DummyKnowledgeBase()
    
    def _init_memory(self):
        """Initialize the conversation memory"""
        if not AI_AVAILABLE:
            return self._create_dummy_memory()
            
        try:
            from langchain.memory import ConversationBufferMemory
            return ConversationBufferMemory(return_messages=True)
        except ImportError as e:
            logger.warning(f"LangChain not available for memory: {e}")
            return self._create_dummy_memory()
    
    def _create_dummy_memory(self):
        """Create a dummy memory for when LangChain is not available"""
        class DummyMemory:
            def __init__(self):
                self.chat_memory = []
                
            def save_context(self, inputs, outputs):
                self.chat_memory.append((inputs, outputs))
                
            def load_memory_variables(self, inputs):
                return {"history": "\n".join([f"{k}: {v}" for k, v in self.chat_memory])}
                
        return DummyMemory()
    
    def _init_conversation(self):
        """Initialize the conversation chain"""
        if not AI_AVAILABLE:
            return self._create_dummy_conversation()
            
        try:
            from langchain.chains import ConversationChain
            from langchain.prompts import PromptTemplate
            
            # Create a prompt template
            prompt = PromptTemplate(
                input_variables=["history", "input"],
                template=self._get_system_prompt() + "\n\nCurrent conversation:\n{history}\nHuman: {input}\nAI:"
            )
            
            return ConversationChain(
                llm=self.llm,
                prompt=prompt,
                memory=self.memory,
                verbose=True
            )
        except ImportError as e:
            logger.warning(f"LangChain not available: {e}")
            return self._create_dummy_conversation()
    
    def _create_dummy_conversation(self):
        """Create a dummy conversation for when LangChain is not available"""
        class DummyConversation:
            def __init__(self):
                self.memory = []
                
            def predict(self, input_text, **kwargs):
                self.memory.append(("Human", input_text))
                response = "I'm running in simple mode. Please install AI dependencies for full functionality.\n\n" \
                         "To enable AI features, install with: pip install torch transformers sentence-transformers langchain"
                self.memory.append(("AI", response))
                return response
                
            def __call__(self, input_text, **kwargs):
                return self.predict(input_text, **kwargs)
                
        return DummyConversation()
    
    def _load_custom_instructions(self) -> Dict:
        """Load custom instructions from file"""
        try:
            with open("config/custom_instructions.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default instructions if file doesn't exist or is invalid
            return {
                "system_prompt": "You are a helpful AI assistant.",
                "language": "en",
                "tone": "friendly"
            }
            
    def _get_system_prompt(self) -> str:
        """Get the system prompt based on current settings"""
        return self.custom_instructions.get("system_prompt", "You are a helpful AI assistant.")
    
    def set_language(self, language: str):
        """Set the conversation language"""
        os.makedirs("data/chat_history", exist_ok=True)
        file_path = f"data/chat_history/chat_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
    
    def get_chat_history(self, limit: int = 10) -> List[Dict]:
        """Get recent chat history"""
        return self.chat_history[-limit:]
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory.clear()
        return "Conversation memory cleared."
    
    def add_to_knowledge(self, text: str, metadata: Optional[Dict] = None):
        """Add information to the knowledge base"""
        from langchain.docstore.document import Document
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        docs = [Document(page_content=text, metadata=metadata or {})]
        splits = text_splitter.split_documents(docs)
        
        # Add to vector store
        self.knowledge_base.add_documents(splits)
        self.knowledge_base.persist()
        
        return f"Added {len(splits)} chunks to knowledge base."

# Singleton instance
chat_manager = AIChatManager()

def get_chat_manager() -> AIChatManager:
    """Get the global chat manager instance"""
    return chat_manager
